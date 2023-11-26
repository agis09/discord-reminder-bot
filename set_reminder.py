import os
import discord
from discord import Intents, Client, Interaction, SelectOption
from discord.ui import Select, View
from discord.app_commands import CommandTree
from dotenv import load_dotenv


load_dotenv()


class MyClient(Client):
    def __init__(self, intents: Intents) -> None:
        super().__init__(intents=intents)
        self.tree = CommandTree(self)

    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"login: {self.user.name} [{self.user.id}]")


intents = Intents.default()
client = MyClient(intents=intents)

TIMEOUT = 30

month: int = 0
day: int = 0
remind_contents: str = ""
remind_user: discord.User | None = None


class SelectMonthView(View):
    options = [SelectOption(label=f"{i}月", value=f"{i}") for i in range(1, 13)]

    def __init__(self, timeout: int):
        super().__init__(timeout=timeout)

    @discord.ui.select(
        placeholder="select",
        options=options,
    )
    async def selectMenu(self, interaction: Interaction, select: Select) -> None:
        select.disabled = True
        global month
        month = int(select.values[0])
        view = SelectHalfMonthView(timeout=TIMEOUT)
        await interaction.response.edit_message(view=view)


class SelectHalfMonthView(View):
    options = [
        SelectOption(label="15日より前", value="1"),
        SelectOption(label="15日以降", value="2"),
    ]

    def __init__(self, timeout: int):
        super().__init__(timeout=timeout)

    @discord.ui.select(
        placeholder="select",
        options=options,
    )
    async def selectMenu(self, interaction: Interaction, select: Select) -> None:
        select.disabled = True
        if select.values[0] == "1":
            view = SelectFirstHalfDayView(timeout=TIMEOUT)
            await interaction.response.edit_message(view=view)
        else:
            view = SelectSecondHalfDayView(timeout=TIMEOUT)
            await interaction.response.edit_message(view=view)


class SelectFirstHalfDayView(View):
    options = [SelectOption(label=f"{i}日", value=f"{i}") for i in range(1, 15)]

    def __init__(self, timeout: int):
        super().__init__(timeout=timeout)

    @discord.ui.select(
        placeholder="select",
        options=options,
    )
    async def selectMenu(self, interaction: Interaction, select: Select) -> None:
        select.disabled = True
        global day
        day = select.values[0]
        await interaction.response.edit_message(view=self)
        await set_remind(interaction=interaction, month=month, day=day)


class SelectSecondHalfDayView(View):
    options = [SelectOption(label=f"{i}日", value=f"{i}") for i in range(15, 32)]

    def __init__(self, timeout: int):
        super().__init__(timeout=timeout)

    @discord.ui.select(
        placeholder="select",
        options=options,
    )
    async def selectMenu(self, interaction: Interaction, select: Select) -> None:
        select.disabled = True
        global day
        day = select.values[0]
        await interaction.response.edit_message(view=self)
        await set_remind(interaction=interaction)
        await set_remind(interaction=interaction, month=month, day=day)


@client.tree.command(name="reminder", description="test")
async def reminder(interaction: Interaction, contents: str):
    view = SelectMonthView(timeout=TIMEOUT)
    global remind_contents
    remind_contents = contents
    global remind_user
    remind_user = interaction.user
    print(remind_contents, remind_user)
    await interaction.response.send_message("set_reminder!!!", view=view)


def set_remind(interaction: Interaction, month: int, day: int):
    return interaction.followup.send(
        f"りまいんど -> content:{remind_contents}, user:{remind_user} いん {month}月{day}日！"
    )


client.run(os.getenv("TOKEN"))
