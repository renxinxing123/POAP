import requests
from bs4 import BeautifulSoup as BS
import pandas as pd
import os
import datetime
import re

def parse_weibo_time(time_str):
    """
    尝试将微博发布时间字符串解析成 datetime 对象。
    支持格式：
      1) "YYYY年MM月DD日 HH:MM"  (例如 "2022年03月14日 00:57")
      2) "刚刚"
      3) "YYYY-MM-DD HH:MM"
      4) "YYYY-MM-DD"
      5) "今天 HH:MM"
      6) "xx分钟前"
      7) "xx小时前"

    如果都无法匹配，返回 None。
    """

    # 打印传入的字符串 - 调试用
    print(f"【parse_weibo_time】 解析前: {time_str}")

    # ---------- 1) 匹配 "YYYY年MM月DD日 HH:MM" ----------
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{1,2})', time_str)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        hour = int(match.group(4))
        minute = int(match.group(5))
        dt = datetime.datetime(year, month, day, hour, minute)
        print(f"【parse_weibo_time】 解析后: {dt}")
        return dt

    # ---------- 2) 匹配 "MM月DD日 HH:MM" 格式（无年份）----------
    match = re.search(r'(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{1,2})', time_str)
    if match:
        current_year = datetime.datetime.now().year  # 默认使用当前年份
        month = int(match.group(1))
        day = int(match.group(2))
        hour = int(match.group(3))
        minute = int(match.group(4))
        dt = datetime.datetime(current_year, month, day, hour, minute)
        print(f"【parse_weibo_time】 解析后: {dt}")
        return dt

    # ---------- 3) 处理“刚刚” ----------
    if '刚刚' in time_str:
        dt = datetime.datetime.now()
        print(f"【parse_weibo_time】 解析后: {dt}")
        return dt

    # ---------- 4) 优先解析 "YYYY-MM-DD HH:MM" ----------
    try:
        dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M')
        print(f"【parse_weibo_time】 解析后: {dt}")
        return dt
    except:
        pass

    # ---------- 5) 再解析 "YYYY-MM-DD" ----------
    try:
        dt = datetime.datetime.strptime(time_str, '%Y-%m-%d')
        print(f"【parse_weibo_time】 解析后: {dt}")
        return dt
    except:
        pass

    # ---------- 6) 处理“今天 HH:MM” ----------
    if '今天' in time_str:
        match = re.search(r'今天\s+(\d{1,2}):(\d{1,2})', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            now = datetime.datetime.now()
            dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            print(f"【parse_weibo_time】 解析后: {dt}")
            return dt
        else:
            dt = datetime.datetime.now()
            print(f"【parse_weibo_time】 解析后: {dt}")
            return dt

    # ---------- 7) 处理“xx分钟前” ----------
    match = re.search(r'(\d+)\s*分钟前', time_str)
    if match:
        minutes_ago = int(match.group(1))
        dt = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
        print(f"【parse_weibo_time】 解析后: {dt}")
        return dt

    # ---------- 8) 处理“xx小时前” ----------
    match = re.search(r'(\d+)\s*小时前', time_str)
    if match:
        hours_ago = int(match.group(1))
        dt = datetime.datetime.now() - datetime.timedelta(hours=hours_ago)
        print(f"【parse_weibo_time】 解析后: {dt}")
        return dt

    # ---------- 最后都没匹配到 ----------
    print("【parse_weibo_time】 解析后: None (未知格式)")
    return None


def get_weibo(v_keyword, v_start_time, v_end_time, v_result_file, ):
    # 搜索关键字，搜索起始时间，搜索截止时间，结果文件

    # 先把字符串形式的时间转换为 datetime，用来做严格过滤
    dt_start = datetime.datetime.strptime(v_start_time, '%Y-%m-%d-%H')
    dt_end = datetime.datetime.strptime(v_end_time, '%Y-%m-%d-%H')
    # 如果你想把这个“结束时间”改成包含 xx:59:59，自己加一小步，如：
    # dt_end = dt_end + datetime.timedelta(hours=1) - datetime.timedelta(seconds=1)


    for page in range(1, 50):
        print('开始爬取[从{}到{}],第{}页'.format(v_start_time, v_end_time, page))
        # 请求地址是微博搜索地址
        url = 'https://s.weibo.com/weibo'
        # 请求参数(在Network中）
        # 此时需要weibo网页点击下一页，让信息加载出来，在All下方第一条Payload中查看参数）
        params = {
            'q':v_keyword,
            'typeall':1,
            'suball':1,
            'timescope':'custom:{}:{}'.format(v_start_time, v_end_time),
            'Refer':'g',
            'page':page,
        }

        # 请求头
        h1 = {
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-encoding':'gzip, deflate, br, zstd',
            'accept-language':'zh-CN,zh;q=0.9,en;q=0.8',
            'cookie':'SCF=AiYg3qAhnhJO4uYLpBc4UArOXovMlWHz4OnPneKvDpKTqUF3alcrtur8chfG2MxfQa70AsaFoADkYsGP3EHwq5s.; SUB=_2A25K_EDmDeRhGeFJ6VES9yfJwjWIHXVmcNwurDV8PUNbmtANLW6kkW9NfHC1nHHDqQWZdAnHZVyKqOIbTyDbyWJ_; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WF_Rv7BfUnz3p_uhvisZn745JpX5KzhUgL.FoMNeoe0S0.f1K.2dJLoI77peoeXSKqNPcfadgYt; ALF=02_1746910646; _s_tentry=weibo.com; Apache=2379876944449.6523.1744318670381; SINAGLOBAL=2379876944449.6523.1744318670381; ULV=1744318670396:1:1:1:2379876944449.6523.1744318670381:',
            'priority':'u=0, i',
            'referer':'https://s.weibo.com/weibo?',
            'sec-ch-ua':'"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-mobile':'?0',
            'sec-ch-ua-platform':'"Windows"',
            'sec-fetch-dest':'document',
            'sec-fetch-mode':'navigate',
            'sec-fetch-site':'same-origin',
            'sec-fetch-user':'?1',
            'upgrade-insecure-requests':'1',
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'}
        # 发送请求
        r = requests.get(url, headers=h1, params=params)
        print(r.status_code)

        # 解析页面
        soup = BS(r.text, 'html.parser')
        item_list = soup.find_all('div', {'action-type': 'feed_list_item'})

        # 先在每页开头创建这些列表
        name_list = [] #微博昵称
        create_time_list = [] #发布时间
        source_list = [] #微博来源
        text_list = [] #微博正文
        repost_count_list = [] #转发数
        comment_count_list = []  #评论数
        like_count_list = []  #点赞数

        for item in item_list:
            name = item.find('p', {'node-type': 'feed_list_content'}).get('nick-name')

            create_time_str = item.find('div', {'class': 'from'}).text.strip().split('来自')[0].strip()
            dt = parse_weibo_time(create_time_str)
            if (dt is None) or (dt < dt_start) or (dt > dt_end):
                # 如果时间无效/不在范围，直接跳过
                continue

            # 只有当微博时间满足条件时，再去解析其他字段
            try:
                source = item.find('div', {'class': 'from'}).text.strip().split('来自')[1].strip()
            except:
                source = '无'

            # 判断是否有“全文”
            if item.find('p', {'node-type': 'feed_list_content_full'}):
                text = item.find('p', {'node-type': 'feed_list_content_full'}).text.strip()
            else:
                text = item.find('p', {'node-type': 'feed_list_content'}).text.strip()

            # 添加过滤条件，确保正文中包含完整的关键词
            if v_keyword not in text:
                continue

            card_act_li = item.find('div', {'class': 'card-act'}).find_all('li')
            repost_count = card_act_li[0].text.strip()
            comment_count = card_act_li[1].text.strip()
            like_count = card_act_li[2].text.strip()

            # 确定这条微博在时间范围内 -> 一次性 append 到各列表
            name_list.append(name)
            create_time_list.append(create_time_str)
            source_list.append(source)
            text_list.append(text)
            repost_count_list.append(repost_count)
            comment_count_list.append(comment_count)
            like_count_list.append(like_count)

            print('微博正文：', text)

        #保存数据
        df = pd.DataFrame(
            {
                '页码': [page] * len(name_list),
                '微博昵称': name_list,
                '发布时间': create_time_list,
                '微博来源': source_list,
                '转发数': repost_count_list,
                '评论数': comment_count_list,
                '点赞数': like_count_list,
                '微博正文': text_list,
            }
        )
        if os.path.exists(v_result_file): #如果文件存在，不再设置表头
            header = False
        else: #否则，设置csv文件表头
            header = True
        df.to_csv(v_result_file, mode='a+', index=False, header=header, encoding='utf_8_sig')
        print(f'第 {page} 页结果保存成功 -> {v_result_file}')
    else:
        print(f'第 {page} 页没有符合时间范围的微博数据，跳过写入。')



def run_weibo_crawl(year, month, day, keyword):
    """
    运行微博爬虫，根据传入的年月日和关键字对该天的24小时进行爬取，
    并将结果保存到一个以 '微博数据_' 开头的 CSV 文件中。
    返回生成的 CSV 文件名。
    """
    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    csv_filename = '微博数据_{}.csv'.format(now)
    start_time = datetime.datetime(year, month, day, 0)
    
    # 每小时为一个时间段，共爬取24小时
    for i in range(24):
        get_weibo(
            v_keyword=keyword,
            v_start_time=(start_time + datetime.timedelta(hours=i)).strftime('%Y-%m-%d-%H'),
            v_end_time=(start_time + datetime.timedelta(hours=i+1)).strftime('%Y-%m-%d-%H'),
            v_result_file=csv_filename
        )
    return csv_filename

