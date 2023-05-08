# dont use discord.py use the fork `pip install discord.py-self`

import os
import json
import nltk
import openai
import discord  # use the discord.py-self verrsion
from dotenv import load_dotenv
nltk.download('punkt')

# load .env
load_dotenv()

# 获取变量
discord_token = os.getenv("DISCORD_TOKEN")
channelIds_forward  = json.loads(os.getenv("FORWARD"))["forward"]
channelIds_listen  = json.loads(os.getenv("LISTEN"))["listen"]
API_KEY = os.getenv("API_KEY")

openai.api_key = API_KEY

# store the chat
sentences = []

# use nltk to deal the context
def deal_context(sentences):

    merged_sentence = ' '.join(sentences)

    tokens = nltk.word_tokenize(merged_sentence)

    detokenized_sentence = nltk.treebank.TreebankWordDetokenizer().detokenize(tokens)

    return detokenized_sentence

#  ChatGPT
class ChatGPT:
    def __init__(self, user):
        self.user = user
        self.messages = [
            {"role": "system", "content": "I'm a college student with a gentle personality who develops in go react and also an open source enthusiast, all in web3. I love everything interesting."}
        ]
        self.filename="jokereven.json"

    def ask_gpt(self):
        # q = "用python实现：提示手动输入3个不同的3位数区间，输入结束后计算这3个区间的交集，并输出结果区间"
        rsp = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=self.messages
        )
        return rsp.get("choices")[0]["message"]["content"]


    def write_to_json(self):
        try:
            # file exist
            if not os.path.exists(self.filename):
                with open(self.filename, "w") as f:
                    # create file
                    pass
            # read
            with open(self.filename, 'r', encoding='utf-8') as f:
                content = f.read()
                msgs = json.loads(content) if len(content) > 0 else {}
            # add
            msgs.update({self.user : self.messages})
            # write
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(msgs, f)
        except Exception as e:
            print(f"write_to_json failed error:{e}")


class MyClient(discord.Client):

    user_name = 'jackineven'
    jokereven = ChatGPT(user=user_name)

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):
        # check if message channel is monitored
        if str(message.channel.id) not in channelIds_listen:
            return

        # message
        print(message)
        print("content:", message.content)
        print("type:", message.type)

        # check if is reply
        replyMessageId = ""

        # type: MessageType.default or MessageType.reply
        if message.type == "MessageType.reply":
            # get reply to message
            replyMessageId = str(message.id)

        # create embed
        embed = discord.Embed(title="redirected from `" + message.channel.name + "`", description=str(message.content), color=0x00ff00)
        embed.set_author(name=str(message.author))
        embed.set_footer(text="# " + str(message.id)) # set message id as footer

        for channelId in channelIds_forward:
            channel_forward = self.get_channel(int(channelId))

            # check if is not reply
            if replyMessageId == "":
                # is not response just send message
                # message is not empty
                if message.content:
                    sentences.append(message.content)
                    if len(sentences) == 6:
                        value = deal_context(sentences)
                        self.jokereven.messages.append({"role": "user", "content": value})
                        answer = self.jokereven.ask_gpt()
                        await channel_forward.send(content=answer)
            else :
                # is reply, search for message
                foundMessageToReply = False
                embed.set_footer(text="# " + str(message.id) + " replyed to # " + replyMessageId) # set reply message

                messages_forward = channel_forward.history(limit=50)
                print('messages_forward:', messages_forward)
                async for messageToReply in messages_forward:
                    for embedForward in messageToReply.embeds:

                        print(embedForward)

                # if didn't find messages_forward to reply to just send message (don't reply)
                if not foundMessageToReply:
                    sentences.append(message.content)
                    if len(sentences) == 6:
                        value = deal_context(sentences)
                        self.jokereven.messages.append({"role": "user", "content": value})
                        answer = self.jokereven.ask_gpt()
                        await channel_forward.send(content=answer)

MyClient().run(discord_token)
