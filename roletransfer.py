import discord
from redbot.core import commands

# --- Configuration ---
# These are the IDs you provided.
REQUIRED_ROLE_ID = 1004617849807065168  # Role required to use the command
QUARANTINE_ROLE_ID = 1066682086490128424 # Role given to the old member

# --- Custom Permission Check ---
# This check ensures only users with the required role can run the command.
def has_transfer_permissions():
    async def predicate(ctx: commands.Context):
        if not ctx.guild or not isinstance(ctx.author, discord.Member):
            return False
        
        author_role_ids = {role.id for role in ctx.author.roles}
        return REQUIRED_ROLE_ID in author_role_ids
    return commands.check(predicate)


class RoleTransfer(commands.Cog):
    """A cog to transfer roles from one member to another."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @has_transfer_permissions() # Apply the custom permission check
    @commands.bot_has_permissions(manage_roles=True) # Check if the bot has the base permission
    async def transferroles(self, ctx: commands.Context, old_member: discord.Member, new_member: discord.Member):
        """
        Copies roles from an old member to a new member, then quarantines the old member.
        """

        # --- Initial Safety Checks ---
        # 1. Prevent transferring roles from a user with the required moderator role
        if any(role.id == REQUIRED_ROLE_ID for role in old_member.roles):
            return await ctx.send("Error: You cannot transfer roles from a member who has the moderator role.")

        # 2. Prevent transferring roles from yourself (redundant with the above check, but good practice)
        if old_member.id == ctx.author.id:
            return await ctx.send("Error: You cannot transfer roles from yourself.")

        # 3. Prevent transferring roles if the old member has an admin role
        if any(role.permissions.administrator for role in old_member.roles):
            return await ctx.send("Error: This command cannot be used on a member who has a role with Administrator permissions.")

        # 4. Ensure the bot can manage the roles
        roles_to_transfer = [role for role in old_member.roles if not role.is_default() and role < ctx.guild.me.top_role]
        if not roles_to_transfer:
            return await ctx.send(f"There are no roles on {old_member.mention} that I can manage.")

        quarantine_role = ctx.guild.get_role(QUARANTINE_ROLE_ID)
        if not quarantine_role:
            return await ctx.send(f"Error: The quarantine role with ID `{QUARANTINE_ROLE_ID}` was not found.")
        if quarantine_role >= ctx.guild.me.top_role:
            return await ctx.send("Error: The quarantine role is higher than my top role, so I cannot assign it.")

        # --- Role Transfer Logic ---
        try:
            # 1. Add roles to the new member
            await new_member.add_roles(*roles_to_transfer, reason=f"Roles transferred from {old_member.display_name} by {ctx.author.display_name}")

            # 2. Remove roles from the old member
            await old_member.remove_roles(*roles_to_transfer, reason=f"Roles transferred to {new_member.display_name} by {ctx.author.display_name}")

            # 3. Add the quarantine role to the old member
            await old_member.add_roles(quarantine_role, reason=f"Quarantined after role transfer by {ctx.author.display_name}")

        except discord.Forbidden:
            return await ctx.send("I do not have sufficient permissions or my role is too low in the hierarchy to perform this action.")
        except Exception as e:
            return await ctx.send(f"An unexpected error occurred: {e}")

        # --- Confirmation ---
        await ctx.send(f"✅ All manageable roles from **{old_member.display_name}** have been moved successfully to **{new_member.display_name}**.")

