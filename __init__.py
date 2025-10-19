from .roletransfer import RoleTransfer

async def setup(bot):
    await bot.add_cog(RoleTransfer(bot))
