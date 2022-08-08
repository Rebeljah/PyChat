
class User:
    def __init__(self, stream):
        self.stream = stream
    
    async def listen(self):
        await self.stream.listen()

    async def cleanup(self):
        await self.stream.close_connection()