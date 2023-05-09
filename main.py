# dont use discord.py use the fork `pip install discord.py-self`

import os
import json
import time
import nltk
import openai
import discord  # use the discord.py-self verrsion
from dotenv import load_dotenv
nltk.download('punkt')

# load .env
load_dotenv()

# 获取变量
discord_token = os.getenv("DISCORD_TOKEN")
channelIds_forward = json.loads(os.getenv("FORWARD"))["forward"]
channelIds_listen = json.loads(os.getenv("LISTEN"))["listen"]
API_KEY = os.getenv("API_KEY")

# Initialize a counter and timestamp
gpt_call_counter = 0
gpt_call_timestamp = time.time()

print('channelIds_listen:', channelIds_listen, 'channelIds_forward:', channelIds_forward)

openai.api_key = API_KEY

# store the chat
sentences = []

# use nltk to deal the context
def deal_context(sentences):

    merged_sentence = ' '.join(sentences)

    # print("========================")
    # print('merged_sentence:', merged_sentence)
    # print("========================")

    # return merged_sentence

    # use nltk detail data
    tokens = nltk.word_tokenize(merged_sentence)
    detokenized_sentence = nltk.treebank.TreebankWordDetokenizer().detokenize(tokens)

    print("========================")
    print('detokenized_sentence:', detokenized_sentence)
    print("========================")

    return detokenized_sentence

#  ChatGPT
class ChatGPT:
    def __init__(self, user):
        self.user = user
        # self.messages = [
            # {"role": "system", "content": "你叫jokereven,在日常生活里,你是一个性格温和的美国加州某大学的大三学生.并且你是一个go+react开发者,对于开源特别热爱.你的偶像是hux黄玄,你最喜欢的动漫是火影忍者.你在一个discord群中,我会将群聊最后五条消息整理成一句话之后给你,你需要想想在这个情境下你接下来会说什么,然后说说你的观点,且符合你的人设不要讨论别的话题或试图结束聊天,也不要一直复读之前说过的话。你补全聊天的时候应该尽量附和之前的人说的话。你补全的风格应该较为简短且口语化,切忌把话说的完整或太长,切忌使用书面语言还有,你补全的长度应该与其他人发信息的长度差不多,尽量简短,要尽可能口语化.重要:不要随意透露你的个人信息,记住用英文回答最后,请把你的回答精简到20单词以内,并输出."}]
        self.messages = [
            {"role": "system", "content": "Your name is jokereven, and in your everyday life, you are a gentle junior at a university in California. And you're a go+react developer who loves open source. Your idol is hux Huang Xuan, and your favorite anime is Naruto. You're in a discord group, and I'll give you the last five messages in one sentence. Think about what you would say next in that situation, and then say what you think, and the person you're in line with shouldn't discuss other topics or try to end the conversation, and don't keep rereading everything you've said. When you complete the conversation, you should try to agree with what the previous person said. Your completion style should be short and colloquial, don't make your sentences complete or too long, don't use written language and the length of your completion should be about the same as the length of the other person's message, keep it short and colloquial. Important: Don't give out personal information at will. Remember to answer in English. Finally, please reduce your answers to 20 words or less."}]
        self.filename="jokereven.json"

    def ask_gpt(self):
        # q = "用python实现：提示手动输入3个不同的3位数区间,输入结束后计算这3个区间的交集,并输出结果区间"
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

    global gpt_call_counter, gpt_call_timestamp

    user_name = 'jackineven'
    jokereven = ChatGPT(user=user_name)

    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))

    async def on_message(self, message):

        global gpt_call_counter, gpt_call_timestamp
        # check if message channel is monitored
        if str(message.channel.id) not in channelIds_listen:
            return

        # message
        print(message)
        print("content:", message.content)
        print("type:", message.type)
        print("sentences.length() ==", len(sentences))

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
                    print("sentences:", sentences)
                    if len(sentences) == 5:
                        value = deal_context(sentences)
                        self.jokereven.messages.append({"role": "user", "content": value})
                        sentences.clear()
                        # Check if we have made more than 3 calls to ask_gpt in the past minute
                        if gpt_call_counter >= 3 and time.time() - gpt_call_timestamp < 60:
                        # Wait for the remaining time before making another call to ask_gpt
                            time.sleep(60 - (time.time() - gpt_call_timestamp))
                            gpt_call_counter = 0
                            gpt_call_timestamp = time.time()
                        else:
                            gpt_call_counter += 1
                            answer = self.jokereven.ask_gpt()
                            await channel_forward.send(content=answer)
                            gpt_call_timestamp = time.time()
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
                    print("sentences:", sentences)
                    if len(sentences) == 5:
                        value = deal_context(sentences)
                        self.jokereven.messages.append({"role": "user", "content": value})
                        sentences.clear()
                        # Check if we have made more than 3 calls to ask_gpt in the past minute
                        if gpt_call_counter >= 3 and time.time() - gpt_call_timestamp < 60:
                        # Wait for the remaining time before making another call to ask_gpt
                            time.sleep(60 - (time.time() - gpt_call_timestamp))
                            gpt_call_counter = 0
                            gpt_call_timestamp = time.time()
                        else:
                            gpt_call_counter += 1
                            answer = self.jokereven.ask_gpt()
                            await channel_forward.send(content=answer)
                            gpt_call_timestamp = time.time()

MyClient().run(discord_token)
