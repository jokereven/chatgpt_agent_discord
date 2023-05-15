import os
import re
import sys
import json
import time
import nltk
import openai
import logging
import discord  # use the discord.py-self verrsion
from dotenv import load_dotenv
nltk.download('punkt')

# load .env
load_dotenv()

# get variables from .env
chat_len = os.getenv("TEMP")
discord_token = os.getenv("DISCORD_TOKEN")
channelIds_forward = json.loads(os.getenv("FORWARD"))["forward"]
channelIds_listen = json.loads(os.getenv("LISTEN"))["listen"]
API_KEY = os.getenv("API_KEY")

# Initialize a counter and timestamp
gpt_call_counter = 0
gpt_call_timestamp = time.time()

print('channelIds_listen:', channelIds_listen, 'channelIds_forward:', channelIds_forward)

openai.api_key = API_KEY

# store the chat when sentences have some data then deal the data and send to gpt
sentences = []

# setup logging
def setup_logging(log_file):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create one output to console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    # create one output to file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger

logging = setup_logging('DEBUG.log')

def journal(information):
    logging.debug(information)


# use nltk to deal the context
def deal_context(sentences):

    merged_sentence = ' '.join(sentences)

    journal("========================")
    journal('merged_sentence:' + merged_sentence)
    journal("========================")

    return merged_sentence

    # use nltk to deal data
    # tokens = nltk.word_tokenize(merged_sentence)
    # detokenized_sentence = nltk.treebank.TreebankWordDetokenizer().detokenize(tokens)

    # print("========================")
    # print('detokenized_sentence:', detokenized_sentence)
    # print("========================")

    # return detokenized_sentence

#  ChatGPT
class ChatGPT:
    def __init__(self, user):
        self.user = user
        # self.messages = [
            # {"role": "system", "content": "你叫jokereven,在日常生活里,你是一个性格温和的美国加州某大学的大三学生,并且你是一个go+react开发者,同时对于开源特别热爱.你的偶像是hux黄玄,同时对生活充满热爱,对一切有趣的事感兴趣.你在一个discord群中,我会以'A:xxx B:xxx C:xxx D:xxx 你:?'的格式输入不全的聊天记录你需要想想在这个情境下你接下来会说什么,然后补充'你:?'中你说的话你补全的话题应该主要与聊天记录的最后三句相关,且符合你的人设不要讨论别的话题或试图结束聊天,也不要一直复读之前说过的话.你补全聊天的时候应该尽量附和之前的人说的话.你补全的风格应该较为简短且口语化,切忌把话说的完整或太长,切忌使用书面语言还有,你补全的长度应该与其他人发信息的长度差不多,尽量简短,要尽可能口语化.重要:不要随意透露你的个人信息.记住用英文回答最后,请把你的回答精简到12单词以内,并输出."}]
        self.messages = [
            {"role": "system", "content": "Your name is jokereven. In everyday life, you are a gentle junior at a university in California, and you are a go+react developer who loves open source. Your idol is hux Hwang Xuan. You also have a great love for life and are interested in anything interesting. If you're in A discord group, I'd start with 'A:xxx B:xxx C:xxx D:xxx You:? You need to think about what you would say next in this situation and then add 'you :? The topics you complete should be mainly related to the last three sentences of the conversation, and the person who meets you should not discuss other topics or try to end the conversation, and don't keep rereading what you said. When you complete the conversation, you should try to agree with what the previous person said. Your completion style should be short and colloquial, don't make your sentences complete or too long, don't use written language and the length of your completion should be about the same as the length of the other person's message, keep it short and colloquial. Important: Don't give out your personal information. Remember to answer in English. At the end, please reduce your answer to 12 words or less and print it."}]
        self.filename="jokereven.json"

    def ask_gpt(self):
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

    user_name = 'jokereven'
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
            if replyMessageId == "" and message.author.name != 'jokereven':
                # is not response just send message
                # message is not empty
                if message.content:
                    sentences.append(f"{message.author.name}:{message.content}")
                    journal("sentences:" + str(sentences))
                    if len(sentences) == int(chat_len):
                        sentences.append("You:?")
                        journal("You:?")
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
                            if 'ai' in answer.lower():
                                await channel_forward.send(content="?")
                                return
                            journal('answer:' + answer)
                            joke = re.split(r'[.,?!:;]+\s*', answer)
                            joke = [s.strip() for s in joke]
                            for s in joke:
                                print('s:', s)
                                if not s or 'jokereven' in s:
                                    continue
                                time.sleep(len(s)/8)
                                await channel_forward.send(content=s)
                            gpt_call_timestamp = time.time()
            else :
                # is reply, search for message
                foundMessageToReply = False
                embed.set_footer(text="# " + str(message.id) + " replyed to # " + replyMessageId) # set reply message

                messages_forward = channel_forward.history(limit=50)
                journal('messages_forward:' + str(messages_forward))
                async for messageToReply in messages_forward:
                    for embedForward in messageToReply.embeds:

                        journal('embedForward:' + str(embedForward))

                # if didn't find messages_forward to reply to just send message (don't reply)
                if not foundMessageToReply:
                    sentences.append(f"{message.author.name}:{message.content}")
                    journal("sentences:" + str(sentences))
                    if len(sentences) == int(chat_len):
                        sentences.append("You:?")
                        journal("You:?")
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
                            # 防止输出含有AI的回答
                            if 'ai' in answer.lower():
                                await channel_forward.send(content="?")
                                return
                            journal('answer:' + answer)
                            joke = re.split(r'[.,?!:;]+\s*', answer)
                            joke = [s.strip() for s in joke]
                            for s in joke:
                                print('s:', s)
                                if not s or 'jokereven' in s:
                                    continue
                                time.sleep(len(s)/8)
                                await channel_forward.send(content=s)
                            gpt_call_timestamp = time.time()

MyClient().run(discord_token)
