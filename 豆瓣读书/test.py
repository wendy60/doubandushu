import pandas as pd
from pylab import mpl

mpl.rcParams['font.sans-serif'] = ['FangSong']  # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题


def get_data():
    filename = 'result.csv'
    data_csv = pd.read_csv(filename, encoding='gbk')
    return data_csv


data = get_data()

print(data.score)
print(data[data['year'] == 1996])
