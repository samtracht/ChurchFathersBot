from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
from responses import get_response, get_response_ai


load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")


intents: Intents = Intents.default()
intents.message_content = True
client: Client = Client(intents=intents)

message: Message = Message


async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print("message was empty because intents were not enabled")
        return

    if user_message[:6] == "!askai":
        print("Running AI Response")
        user_message = user_message[6:]

        response: str = get_response_ai(user_message)
        print(len(response))
        try:
            await message.channel.send(response)
        except Exception as e:
            print(e)

    elif user_message[:4] == "!ask":
        print("Running Citation Response")
        user_message = user_message[4:]

        response: str = get_response(user_message)

        for i in response:
            try:
                r = f"**Citation**:\n- {i['metadata']['citation']}\n**Text**:\n- {i['metadata']['text']}\n\n\n"
                await message.channel.send(r)
            except Exception as e:
                print(e)


# Handing Start up for bot


@client.event
async def on_ready() -> None:
    print(f"{client.user} is now running!")


@client.event
async def on_message(message: Message) -> None:
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel: str = str(message.channel)

    await send_message(message, user_message)


def main() -> None:
    client.run(token=TOKEN)


if __name__ == "__main__":
    main()
