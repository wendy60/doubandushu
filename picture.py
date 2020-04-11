import pyecharts


def create_Bar():
    bar = pyecharts.Bar("全国各地最高气温", "2018-4-18", title_color='red', title_pos='right', width=1400, height=700,
                        background_color='#404a59')
    bar.add("最高气温", mark_point=['max', 'min', 'average'], is_label_show=True, is_datazoom_show=True, legend_pos='left')
    bar.render('Bar-High.html')
