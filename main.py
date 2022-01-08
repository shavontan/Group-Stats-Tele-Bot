import os
import telebot
from telebot.types import BotCommand
from replit import db
import numpy as np
import pandas as pd
from pandas import Series, DataFrame
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import heapq
import squarify 
import random

API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY)

##### Bot commands on the menu icon #####
commands = [
BotCommand('greet', 'Say hi'),
BotCommand('help', 'Learn what you can do with this bot'),
BotCommand('msgfrequency', 'Who always reply and who always MIA'),
BotCommand('stickerfrequency', 'Who are the sticker lovers (or haters)'),
BotCommand('ourmostusedsticker', 'Your group\'s favourite sticker'),
BotCommand('mymostusedsticker', 'Your favourite sticker'),
BotCommand('mymostusedwords', 'Words your friends are sick of hearing from you'),
BotCommand('avgwords', 'Avg number of words per msg'),
BotCommand('textorsticker', 'Use text or sticker more'),
BotCommand('f', 'Press f to pay respects to Ahma'),
]
bot.set_my_commands(commands)

##### Commands #####
@bot.message_handler(commands=['greet'])
def greet(message):
  bot.reply_to(message, "You call me for what?")

@bot.message_handler(commands=['f'])
def payrespect(message):
  bot.reply_to(message, "OI I haven't die yet la!")

@bot.message_handler(commands=['help'])
def help(message):
  bot.reply_to(message, "Harlo I am Sassy Stats Ahma! Dun think I old brain no good!\n\nUse this list of commands to learn about your group's texting habits and I'll send you my personal insights free-of-charge:\n\n/msgfrequency - See who active or who never talk lor\n/mymostusedwords - I tell you the words people so sian of hearing from you\n/stickerfrequency - See who like to stick stickers all the time.\n/ourmostusedsticker - I tell you your group's favourite sticker lor\n/mymostusedsticker - I tell you your favourite sticker lor\n/avgwords - See your average text length lor\n/textorsticker - I tell you who like to stick sticker and who like to text")

@bot.message_handler(commands=['msgfrequency'])
def msgfrequency(message):
  data = []
  names = []
  chat_id = str(message.chat.id)
  for person in db[chat_id].keys():
    data.append(len(db[chat_id][person]["history"]))
    names.append(db[chat_id][person]["first_name"])
  
  zipped_lists = zip(data, names)
  sorted_pairs = sorted(zipped_lists, reverse=True)
  tuples = zip(*sorted_pairs)
  data, names = [list(tup) for tup in tuples]


  all_colors = list(plt.cm.colors.cnames.keys())
  random.seed(100)
  c = random.choices(all_colors, k=len(names))

  plt.bar(names, data, color=c)
  plt.title("Who's Most Active in this Group?")
  plt.ylabel('Total Number of Messages Sent')
  plt.xlabel('Name')
  chat_id = str(message.chat.id)

  # should ideally save to some cloud db instead of locally
  plt.savefig(chat_id)
  plt.clf()
  bot.send_photo(message.chat.id, photo=open(f'{chat_id}.png', 'rb'))

  winners = ', '.join(find_winners(data, names))

  bot.send_message(message.chat.id, "{}, go get a life!".format(winners))


@bot.message_handler(commands=['avgwords'])
def avgWordsPerMsg(message):
  data = [] # avg. num words
  names = []
  numWords = [] # 2D array
  smallest = 9999
  largest = 0

  chat_id = str(message.chat.id)
  for person in db[chat_id].keys():
    history = db[chat_id][person]["history"]
    wordLengths = []
    for sentence in history:
      length = len(sentence.split())
      wordLengths.append(length)

      if length < smallest:
        smallest = length
      if length > largest:
        largest = length

    avg = sum(wordLengths) / len(wordLengths)
    data.append(avg)

    numWords.append(wordLengths)

    names.append(db[chat_id][person]["first_name"])
  
  zipped_lists = zip(data, names, numWords)
  sorted_pairs = sorted(zipped_lists, reverse=True)
  tuples = zip(*sorted_pairs)
  data, names, numWords = [list(tup) for tup in tuples]


  all_colors = list(plt.cm.colors.cnames.keys())
  random.seed(100)
  c = random.choices(all_colors, k=len(names))

  # vertical barplot
  # plt.bar(names, data, color=c)
  # plt.title("Who Sends the Longest Message?")
  # plt.ylabel('Av. number of words per msg')
  # plt.xlabel('Name')

  # horizontal barplot
  # plt.barh(names, data, color=c)
  # plt.title("Who Sends the Longest Message?")
  # plt.ylabel('Name')
  # plt.xlabel('Av. number of words per msg')

  # # violin plot
  fig, ax = plt.subplots()
  vp = ax.violinplot(numWords)
  ax.set(
      xticks=range(1, len(names)+1),
      xticklabels=names,)

  for pc in vp['bodies']:
    pc.set_facecolor(random.choices(all_colors, k=1))
    pc.set_edgecolor('black')
  plt.title("Who Sends the Longest Message?")
  plt.ylabel('Av. Number of Words per Msg')
  plt.xlabel('Name')
      

  plt.savefig(chat_id)
  plt.clf()
  bot.send_photo(message.chat.id, photo=open(f'{chat_id}.png', 'rb'))

  info_string = ""
  for i in range (len(names)):
    info_string = info_string + names[i] + " sends an avg of " + str(round(data[i], 2)) + " words per msg\n"

  winners = ', '.join(find_winners(data, names))

  bot.send_message(message.chat.id, "{}\n{}, you more naggy than my grandmother!".format(info_string, winners))
    

@bot.message_handler(commands=['mymostusedwords'])
def myMostUsedWords(message):

  chat_id = str(message.chat.id)
  user_id = str(message.from_user.id)
  name = db[chat_id][user_id]["first_name"]
  history = db[chat_id][user_id]["history"]
  
  exclude = ['the', 'of', 'a', 'an', 'am', 'she', 'he', 'her', 'his', 'him', 'hers', 'this', 'that', 'these', 'those', 'it', 'its', 'ours', 'our', 'theirs', 'their', 'them', 'there', 'i', 'my', 'yours', 'your', 'but', 'it\'s', "it’s", 'to', 'in', 'into', 'is']

  freq = {}
  labels = []
  sizes = []


  for sentence in history:
    
    # cleaning sentence to remove non alphanumeric chars
    for i in range(len(sentence)):
	    if not sentence[i].isalnum():
		    sentence = sentence[:i] + " " + sentence[i+1:]

    # split sentence into words
    wordsList = sentence.split()
    for word in wordsList:
      word = word.lower()
      if word in exclude or len(word) <= 1:
        continue
      if word not in freq.keys():
        freq[word] = 1
      else:
        freq[word] = freq[word] + 1
  

  maxKey = max(freq, key=freq.get)
  listOfMaxKeys = heapq.nlargest(10, freq, freq.get)
  max_words = ', '.join(listOfMaxKeys)

  for word in listOfMaxKeys:
    size = freq[word]
    sizes.append(size)
    label = word + "\n" + "(" + str(size) + ")"
    labels.append(label)


  colors = [plt.cm.Spectral(i/float(len(labels))) for i in range(len(labels))]
  squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.8)
  title = name + "'s Top 10 Most Used Words"
  plt.title(title)
  plt.savefig(chat_id)
  plt.clf()
  bot.send_photo(message.chat.id, photo=open(f'{chat_id}.png', 'rb'))

  # bot.reply_to(message, "{}, your most common word is: {}".format(name, maxKey))
  bot.reply_to(message, "{}, please ah I sian of hearing these words from you liao. Dun say '{}' again pls. Go expand your vocab!".format(name, maxKey))
  
  
@bot.message_handler(commands='stickerfrequency')
def num_stickers(message):
  names = []
  data = []
  chat_id = str(message.chat.id)
  for person in db[chat_id]:
    names.append(db[chat_id][person]["first_name"])
    data.append(db[chat_id][person]["total_stickers"])

  zipped_lists = zip(data, names)
  sorted_pairs = sorted(zipped_lists, reverse=True)
  tuples = zip(*sorted_pairs)
  data, names = [list(tup) for tup in tuples]

  all_colors = list(plt.cm.colors.cnames.keys())
  c = random.choices(all_colors, k=len(names))

  plt.bar(names, data, color=c)
  plt.title("Who sends the most stickers?")
  plt.ylabel('Number of Stickers Sent')
  plt.xlabel('Name')

  plt.savefig(chat_id)
  plt.clf()
  bot.send_photo(message.chat.id, photo=open(f'{chat_id}.png', 'rb'))

  winners = ', '.join(find_winners(data, names))

  bot.send_message(message.chat.id, "{}, your grandmother will be so proud of you, she will buy you a sticker book.".format(winners))

@bot.message_handler(commands='mymostusedsticker')
def myMostUsedSticker(message):
  chat_id = str(message.chat.id)
  user_id = str(message.from_user.id)

  most_used_sticker = ""
  highest_freq = 0
  for pair in db[chat_id][user_id]["stickers"].values():
    if pair[1] > highest_freq:
      highest_freq = pair[1]
      most_used_sticker = pair[0]
    
  bot.send_sticker(chat_id, most_used_sticker)
  bot.send_message(message.chat.id, "You sent this {} times. Why you like it so much?".format(highest_freq))

@bot.message_handler(commands='ourmostusedsticker')
def groupMostUsedSticker(message):
  chat_id = str(message.chat.id)
  
  highest_freq = 0 
  most_used_sticker = "" 
  sticker_dict = {}
  for user_id in db[chat_id]: 
    for sticker, pair in db[chat_id][user_id]["stickers"].items():
      if sticker in sticker_dict:
        sticker_dict[sticker][1] += pair[1]
      else:
        sticker_dict[sticker] = pair
      
      if sticker_dict[sticker][1] > highest_freq:
        highest_freq = sticker_dict[sticker][1]
        most_used_sticker = sticker_dict[sticker][0]
  
  bot.send_sticker(chat_id, most_used_sticker)
  bot.send_message(message.chat.id, "You all sent this {} times! Can change another one?".format(highest_freq))

@bot.message_handler(commands='textorsticker')
def text_sticker_frequnecy(message):
  names = []
  sticker_data = []
  text_data = []
  chat_id = str(message.chat.id)
  
  for person in db[chat_id]:
    names.append(db[chat_id][person]["first_name"])
    sticker_data.append(db[chat_id][person]["total_stickers"])
    text_data.append(len(db[chat_id][person]["history"]))
  
  X_axis = np.arange(len(names))
  
  plt.bar(X_axis - 0.2, text_data, 0.4, label = 'text')
  plt.bar(X_axis + 0.2, sticker_data, 0.4, label = 'stickers')
  
  plt.xticks(X_axis, names)
  plt.xlabel("Name")
  plt.ylabel("Frequency")
  plt.title("Text or Sticker?")
  plt.legend()

  plt.savefig(chat_id)
  plt.clf()
  bot.send_photo(message.chat.id, photo=open(f'{chat_id}.png', 'rb'))
  
##### Storing to database ##### 
# Function that adds message to the database
@bot.message_handler(func=lambda m: True)
def add_message(message):
  print(message)
  chat_id = str(message.chat.id)
  user_id = str(message.from_user.id)
  first_name = str(message.from_user.first_name)
  
  if chat_id not in db.keys():
    db[chat_id] = {user_id: {"first_name": first_name, "history": [message.text], "stickers": {}, "total_stickers": 0}}
  else:
    if user_id in db[chat_id].keys():
      db[chat_id][user_id]["history"].append(message.text)
    else:
      db[chat_id][user_id] = {"first_name": first_name, "history": [message.text], "stickers": {}, "total_stickers": 0}

# Function that adds stickers to the database
@bot.message_handler(content_types="sticker")
def add_sticker(sticker):
  chat_id = str(sticker.chat.id)
  user_id = str(sticker.from_user.id)
  first_name = str(sticker.from_user.first_name)
  file_id = str(sticker.sticker.file_id)
  file_unique_id = str(sticker.sticker.file_unique_id)
  
  if chat_id not in db.keys():
    db[chat_id] = {user_id: {"first_name": first_name, "history": [], "stickers": {file_unique_id: (file_id, 1)}, "total_stickers": 1}}
  else:
    if user_id in db[chat_id].keys():
      if file_unique_id in db[chat_id][user_id]["stickers"]:
        db[chat_id][user_id]["stickers"][file_unique_id][1] += 1
        db[chat_id][user_id]["total_stickers"] += 1
      else:
        db[chat_id][user_id]["stickers"][file_unique_id] = (file_id, 1)
        db[chat_id][user_id]["total_stickers"] += 1
    else:
      db[chat_id][user_id] = {"first_name": first_name, "history": [], "stickers": {file_unique_id: (file_id, 1)}, "total_stickers": 1}
  
##### Helper functions #####
# Function to find the most active group members
def find_winners(data, names):
  max_val = max(data)
  freq = data.count(max_val)
  winners = []
  if freq == 1:
    index = data.index(max_val)
    winners.append(names[index])
  else:
    for i in range(len(data)):
      if data[i] == max_val:
        winners.append(names[i])
  return winners
      
bot.infinity_polling()
