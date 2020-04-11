import csv
import os  ##操作系统交互库
import tkinter as tk
from tkinter import *  ##GUI库
from tkinter import scrolledtext, ttk

import jieba  ##中文分词库
import numpy as np  ##科学计算
import pandas as pd
import pymongo
import requests  ##http请求模块
from bs4 import BeautifulSoup  ##网页解析库
from matplotlib import pyplot as plt  ##绘图库
from pandas import DataFrame  ##数据分析模块
from pylab import mpl
# from config import *
from pymongo import MongoClient
from terminaltables import AsciiTable
from tqdm import tqdm  ##显示进度条
from wordcloud import WordCloud, ImageColorGenerator  ##词云展示第三方库

mpl.rcParams['font.sans-serif'] = 'Songti SC'  # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

URL = 'http://book.douban.com/top250'
path_result = '/Users/kangxiaoran/Desktop/豆瓣读书/豆瓣读书/'

client = pymongo.MongoClient("localhost", 27017)
db = client['local']


# 获取网页原始数据
def download_page(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'
    }
    data = requests.get(url, headers=headers).content
    return data


# 从网页中提取感兴趣文本
def get_information(doc):
    # 空数组，方便之后存取信息
    names = []
    authors = []
    presses = []
    years = []
    prices = []
    scores = []
    nums = []
    quotes = []

    soup = BeautifulSoup(doc, 'html.parser')
    content = soup.find('div', attrs={'class': 'indent'})
    for i in content.find_all('table'):
        # 获取书名
        name = i.find('div', attrs={'class': 'pl2'})
        name = name.find('a').get_text().strip()

        others = i.find('p', attrs={'class': 'pl'}).get_text()
        others = others.split('/')
        # 获取作者
        if '中华书局' in others[0]:
            author = '无'
            press = '中华书局'
            year = '2006'
            price = '9.8元'
        else:
            author = others[0].strip()
            if (('协会' not in others[1]) and ('出版' not in others[1]) and ('书店' not in others[1])):
                # 获取出版社
                press = others[2]
                # 获取出版年份
                year = others[3]
                year = year.split('-')[0]
                # 获取价格
                if len(others) > 4:
                    if 'CNY' in others[4]:
                        price = others[4].split()[1]
                    else:
                        price = others[4].split('元')[0]
                else:
                    price = 0
            else:
                press = others[1]
                # 获取出版年份
                year = others[2]
                year = year.split('-')[0]
                # 获取价格
                if len(others) > 3:
                    if 'CNY' in others[3]:
                        price = others[3].split()[1]
                    else:
                        price = others[3].split('元')[0]
                else:
                    price = 0
        # 获取评分
        score = i.find('span', attrs={'class': 'rating_nums'}).get_text()
        # 获取评价人数
        num = i.find('span', attrs={'class': 'pl'}).get_text()
        num = re.split('\(|人', num)[1].strip()
        # 获取引语
        info = i.find('span', attrs={'class': 'inq'})
        if info:
            quotes.append(info.get_text())
        else:
            quotes.append('无')

        # 开始存储信息
        names.append(name)
        authors.append(author)
        presses.append(press)
        years.append(year)
        prices.append(price)
        scores.append(score)
        nums.append(num)

    # 返回存储信息的数组，方便之后制作表格
    return names, authors, presses, years, prices, scores, nums, quotes


def Data_engineering(URL, path_result):
    # 同上面的原理
    names = []
    authors = []
    presses = []
    years = []
    prices = []
    scores = []
    nums = []
    quotes = []

    for page in tqdm(range(0, 250, 25)):
        url = URL + '?start=' + str(page)
        doc = download_page(url)
        names_part, authors_part, presses_part, years_part, prices_part, scores_part, nums_part, quotes_part = get_information(
            doc)
        names = names + names_part
        authors = authors + authors_part
        presses = presses + presses_part
        years = years + years_part
        prices = prices + prices_part
        scores = scores + scores_part
        nums = nums + nums_part
        quotes = quotes + quotes_part
    L = len(names)
    data = [names, authors, presses, years, prices, scores, nums, quotes]

    data_csv = DataFrame(data, index=['name', 'author', 'press', 'year', 'price', 'score', 'num', 'quote'],
                         columns=np.array(range(L)))
    data_csv = data_csv.T
    if not os.path.exists(path_result):
        os.makedirs(path_result)
    filename = path_result + 'result.csv'
    data_csv.to_csv(filename, index=False, encoding='utf-8-sig')


def get_data():
    filename = 'result.csv'
    data_csv = pd.read_csv(filename, encoding='gbk')
    return data_csv


def connection():
    # 1:连接本地MongoDB数据库服务
    conn = MongoClient("localhost")
    # 2:连接本地数据库(project)。没有时会自动创建
    db = conn.project
    # 3:创建集合
    set1 = db.book
    # 4:看情况是否选择清空(两种清空方式，第一种不行的情况下，选择第二种)
    # 第一种直接remove
    set1.remove(None)
    # 第二种remove不好用的时候
    # set1.delete_many({})
    return set1


def insertToMongoDB(set1):
    # 打开文件result.csv
    with open('/Users/kangxiaoran/Desktop/豆瓣读书/result.csv', 'r', encoding='gbk')as csvfile:
        # 调用csv中的DictReader函数直接获取数据为字典形式
        reader = csv.DictReader(csvfile)
        # 创建一个counts计数一下 看自己一共添加了了多少条数据
        counts = 0
        for each in reader:
            # 将数据中需要转换类型的数据转换类型。原本全是字符串（string）。

            each['price'] = float(each['price'])
            each['score'] = float(each['score'])
            each['num'] = float(each['num'])
            set1.insert(each)
            counts += 1
            print('成功添加了' + str(counts) + '条数据 ')


def data_analyse_button1_figure():
    data = get_data()
    plt.hist(x=data.num, bins=100)
    plt.ylabel('短评数量')
    plt.xlabel('短评数区间分布')
    plt.title('短评频数分布直方图')
    plt.show()


def data_analyse_button2_figure():
    data = get_data()
    plt.hist(x=data.price, bins=100)
    plt.ylabel('价格数量')
    plt.xlabel('价格区间分布')
    plt.title('单价频数分布直方图')
    plt.show()


def data_analyse_button3_figure():
    data = get_data()
    plt.hist(x=data.score, bins=100)
    plt.ylabel('评分数量')
    plt.xlabel('评分区间分布')
    plt.title('评分频数分布直方图')
    plt.show()


def work_cloud_visualization():
    data = get_data()
    words = ''
    word_list = []
    girl_image = plt.imread('girl.jpg')
    wc = WordCloud(background_color='#FFF0F5',  # 背景颜色
                   max_words=1000,  # 最大词数
                   mask=girl_image,  # 以该参数值作图绘制词云，这个参数不为空时，width和height会被忽略
                   max_font_size=100,  # 显示字体的最大值
                   font_path='/System/Library/Fonts/Hiragino Sans GB.ttc',  # 解决显示口字型乱码问题
                   random_state=42,  # 为每个词返回一个PIL颜色
                   # width=1000,  # 图片的宽
                   # height=860  #图片的长
                   )
    for i in data.quote:
        words = words + i
    word_generator = jieba.cut(words, cut_all=False)
    for word in word_generator:
        word_list.append(word)
    text = ' '.join(word_list)
    wc.generate(text)
    # 基于彩色图像生成相应彩色
    image_colors = ImageColorGenerator(girl_image)
    # 显示图片
    plt.imshow(wc)
    # 关闭坐标轴
    plt.axis('off')
    # 绘制词云
    plt.figure()
    plt.imshow(wc.recolor(color_func=image_colors))
    plt.axis('off')
    wc.to_file('19th.png')
    plt.show()


def data_inquire_entry(event=None):
    filename = 'result.csv'
    data = pd.read_csv(filename, encoding='gbk')
    temp1 = e1.get()  # 作者
    temp2 = e2.get()  # 作品
    temp3 = e3.get()  # 评分
    temp4 = e4.get()  # 年代
    temp5 = e5.get()  # 价格范围左
    temp6 = e6.get()  # 价格范围右

    dict = {temp1: 'author', temp2: 'name', temp3: 'score', temp4: 'year'}
    print(dict)
    for i in dict:
        print(i)
        if i == '':
            continue
        else:
            if dict[i] == 'score':
                score = float(i)
                data = data[data['score'] == score]
                print(data)
            elif dict[i] == 'year':  # python特有的else if结构语句
                year = i
                data = data[data['year'] == year]
                print(data)
            else:
                data = data[data[dict[i]] == i]
                print(data)
    print(data)

    if temp5 != '':
        data = data[data['price'] > float(temp5)]
    if temp6 != '':
        data = data[data['price'] < float(temp6)]
    else:
        pass
    inquire = data
    head = list(inquire)
    data_inquire = [head]
    content = inquire.values.tolist()
    for i in range(len(content)):
        data_inquire.append(content[i])
    data_inquire = AsciiTable(data_inquire)
    text.insert(INSERT, data_inquire.table)


def update():
    text.delete(1.0, tk.END)


# 数据工程，负责将数据提取，存储。不爬虫的时候可以注释掉。
# Data_engineering(URL, path_result)


root = Tk()
bl_status = ttk.Label(root, width=20, text="Some Text")
bl_status['background'] = 'yellow'
root.title("豆瓣分析系统")
root.minsize(1000, 800)
# 数据分析模块界面设计
label_analyse = Label(root, text='数据分析', background='cyan').grid(row=1, column=0, padx=50)
anaylse_button1 = Button(root, text='短评数分布', command=lambda: data_analyse_button1_figure()).grid(row=2, column=1)
anaylse_button2 = Button(root, text='价格分布', command=lambda: data_analyse_button2_figure()).grid(row=3, column=1)
anaylse_button3 = Button(root, text='评分分布', command=lambda: data_analyse_button3_figure()).grid(row=4, column=1)
anaylse_button4 = Button(root, text='词云可视化', command=lambda: work_cloud_visualization()).grid(row=5, column=1)
# 数据查询模块
label_inquire = Label(root, text='数据查询', background='yellow').grid(row=1, column=2, padx=50)
inquire_label1 = Label(root, text='按作者查询').grid(row=2, column=3)
inquire_label2 = Label(root, text='按作品查询').grid(row=3, column=3)
inquire_label3 = Label(root, text='按评分查询').grid(row=4, column=3)
inquire_label4 = Label(root, text='按年代查询').grid(row=5, column=3)
inquire_label5 = Label(root, text='按价格查询').grid(row=6, column=3)

# 数据查询输入模块
e1 = StringVar()
en1 = Entry(root, validate='key', textvariable=e1, background='lightgrey')
en1.grid(row=2, column=4)
en1.bind('<Return>', data_inquire_entry)

e2 = StringVar()
en2 = Entry(root, validate='key', textvariable=e2, background='lightgrey')
en2.grid(row=3, column=4)
en2.bind('<Return>', data_inquire_entry)
e3 = StringVar()
en3 = Entry(root, validate='key', textvariable=e3, background='lightgrey')
en3.grid(row=4, column=4)
en3.bind('<Return>', data_inquire_entry)
e4 = StringVar()
en4 = Entry(root, validate='key', textvariable=e4, background='lightgrey')
en4.grid(row=5, column=4)
en4.bind('<Return>', data_inquire_entry)
e5 = StringVar()
en5 = Entry(root, validate='key', textvariable=e5, background='lightgrey')
en5.grid(row=6, column=4)
en5.bind('<Return>', data_inquire_entry)
e6 = StringVar()
en6 = Entry(root, validate='key', textvariable=e6, background='lightgrey')
en6.grid(row=6, column=6)
en6.bind('<Return>', data_inquire_entry)
# 数据显示模块
text = scrolledtext.ScrolledText(root, width=120, height=20, background='pink')
text.grid(row=7, columnspan=7, padx=20, pady=10)

clear_button = Button(root, text='清空', command=lambda: update()).grid(row=8, column=1)

root.mainloop()
