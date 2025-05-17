#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 19:59:29 2025

@author: xinxing
"""

import re
import pandas as pd
import json
import os
from tqdm import tqdm
import csv
import matplotlib.pyplot as plt
from Agents import Coordinator, SentimentAnalysistAgent, TopicModellingAgent, Summarizer
from WeiboCrawler import *

def clean_json_output(response_str: str) -> str:
    """
    清洗 agent 返回的字符串，去除 markdown 代码块标记（例如 ```json 和 ```），确保字符串以 { 开头，以 } 结尾。
    """
    # 使用正则表达式提取代码块内的内容
    pattern = r'```json\s*(\{.*\})\s*```'
    match = re.search(pattern, response_str, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 如果没有匹配到 markdown 格式，则直接返回原字符串
    return response_str.strip()

def merge_and_analyze(sentiment_output, topic_output):
    """
    将 sentiment_output 和 topic_output 两个 CSV 文件进行合并，
    删除“微博正文”和“编号”两列，并删除“topics”列为空的行，
    分别保存中间结果到 merged_output.csv 和 merged_output_cleaned.csv，
    然后统计每个 topics 对应的 sentiment 数量，
    按照各 topic 的总计数降序排序，并绘制分组柱状图。

    参数:
        sentiment_output: 包含情感数据的 CSV 文件路径（前两列和第三列为 sentiment）
        topic_output: 包含主题数据的 CSV 文件路径（前两列和 topics 列）

    返回:
        sentiment_counts: 每个 topics 对应的 sentiment 数量统计 DataFrame
    """
    # 读取 CSV 文件
    sentiment_df = pd.read_csv(sentiment_output, encoding="utf-8")
    topic_df = pd.read_csv(topic_output, encoding="utf-8")
    
    # 假设两个文件的前两列名称完全相同
    common_cols = list(topic_df.columns[:2])
    # 取出 sentiment_output 中的前两列和第三列（假设第三列为 sentiment）
    sentiment_third_col = sentiment_df.columns[2]
    sentiment_subset = sentiment_df[common_cols + [sentiment_third_col]]
    
    # 仅将 sentiment_output 的第三列合并到 topic_df 中（基于前两列）
    merged_df = pd.merge(topic_df, sentiment_subset, on=common_cols, how='left')
    
    # 保存合并结果
    merged_df.to_csv("merged_output.csv", index=False, encoding="utf-8")
    print("合并完成，结果保存在 merged_output.csv")
    
    # 删除“微博正文”和“编号”两列（如果存在）
    merged_df = merged_df.drop(columns=["微博正文", "编号"], errors='ignore')
    
    # 删除“topics”列为空的行（去除空格后判断是否为空字符串或 NaN）
    merged_df = merged_df[merged_df["topics"].notna() & (merged_df["topics"].str.strip() != "")]
    
    # 定义一个字典来累积每个主题的 sentiment 统计
    aggregated_counts = {}

    # 遍历 merged_df 中的每一行数据
    for idx, row in merged_df.iterrows():
        topics_str = row["topics"]
        sentiment = row["sentiment"].strip()  # 预期为 negative、neutral 或 positive
        # 拆分 topics，多个主题以逗号分隔
        topics_list = [t.strip() for t in topics_str.split(",") if t.strip()]
        
        for topic in topics_list:
            if topic not in aggregated_counts:
                aggregated_counts[topic] = {"negative": 0, "neutral": 0, "positive": 0}
            # 累加该 sentiment 的数量
            if sentiment in aggregated_counts[topic]:
                aggregated_counts[topic][sentiment] += 1

    # 将统计结果转换为 DataFrame，并计算总量
    data = []
    for topic, counts in aggregated_counts.items():
        total = counts["negative"] + counts["neutral"] + counts["positive"]
        data.append({
            "topics": topic,
            "negative": counts["negative"],
            "neutral": counts["neutral"],
            "positive": counts["positive"],
            "total": total
        })

    result_df = pd.DataFrame(data)
    # 按 total 从高到低排序
    result_df = result_df.sort_values("total", ascending=False)

    print("每个 topics 对应的 sentiment 数量统计（降序排序）：")
    print(result_df)

    # 保存结果到新的 CSV 文件
    result_df.to_csv("aggregated_topic_sentiment.csv", index=False, encoding="utf-8")
    print("统计结果已保存到 aggregated_topic_sentiment.csv")
    
    # 绘制柱状图（删除 total 列后绘图）
    '''plot_df = sentiment_counts.drop(columns=["total"])
    ax = plot_df.plot(kind="bar", figsize=(12, 6))
    plt.xlabel("Topics")
    plt.ylabel("Counts")
    plt.title("每个 Topics 对应的 Sentiment 数量统计")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="Sentiment")
    plt.tight_layout()
    plt.show()'''
    
    return result_df 

def conversation_loop():
    """
    与用户持续对话，直到 agent 返回包含所有必需信息的 JSON 格式回复，
    此时调用微博爬虫，并返回生成的 CSV 文件名和事件关键字。
    """
    coordinator = Coordinator(prompt_filepath='./prompts/Coordinator_prompt.txt')
    
    while True:
        user_text = input("请输入查询内容：")
        # 调用 Coordinator 处理用户输入
        response = coordinator.run(user_text)
        response = clean_json_output(response)
        print("Agent 回复：", response)
        
        # 尝试解析回复为 JSON 格式
        try:
            result = json.loads(response)
            required_keys = ["event_keywords", "start_year", "start_month", "start_day", "event_release_platform"]
            if all(key in result for key in required_keys):
                platform = result["event_release_platform"].lower()
                if platform not in ["weibo", "微博"]:
                    print("目前服务仅支持微博平台，请重新提供相关信息。")
                    continue

                try:
                    year = int(result["start_year"])
                    month = int(result["start_month"])
                    day = int(result["start_day"])
                except Exception as e:
                    print("时间信息格式有误，请检查后重试。", e)
                    continue

                # 保存事件关键字（列表格式），取第一个关键字作为爬虫关键字
                event_keywords = result["event_keywords"]
                keyword = event_keywords[0].strip("#")
                
                # 回复格式完整时调用爬虫，并返回 CSV 文件名和事件关键字
                csv_file = run_weibo_crawl(year, month, day, keyword)
                print("微博爬虫已启动，爬取任务开始执行。")
                return csv_file, event_keywords
        except json.JSONDecodeError:
            continue


def perform_sentiment_analysis(csv_file: str):
    """
    读取 CSV 文件，分批调用情感分析 agent，
    并累计统计情感结果。同时将每条微博文本及对应的情感写入 "public_opinion.csv" 文件。
    返回 sentiment_counts 字典。
    """
    df = pd.read_csv(csv_file, encoding='utf-8')
    chunk_size = 10
    num_rows = len(df)
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    
    # 输出文件名
    output_file = "sentiment_analysis_output.csv"
    # 检查文件是否存在，若不存在则先创建并写入表头
    if not os.path.exists(output_file):
        with open(output_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["编号", "微博正文", "sentiment"])
    
    for start in tqdm(range(0, num_rows, chunk_size), desc="Processing chunks"):
        # 每个批次重新实例化 agent，避免对话历史过长
        agent = SentimentAnalysistAgent("./prompts/Sentiment_analysist_prompt.txt")
        
        # 取出当前块数据，并为每条微博添加编号
        chunk = df.iloc[start:start + chunk_size].copy()
        chunk.reset_index(drop=True, inplace=True)
        chunk['编号'] = chunk.index + 1
        
        # 拼接每条微博文本（假设 CSV 中的“微博正文”列包含文本）
        query_lines = chunk.apply(lambda row: f"{row['编号']}: {row['微博正文']}", axis=1)
        query = "\n".join(query_lines)
        
        response_str = agent.run(query)
        cleaned_response = clean_json_output(response_str)
        print(cleaned_response)
        
        try:
            response_data = json.loads(cleaned_response)
            # 更新累计情感统计
            summary = response_data.get("summary", {})
            sentiment_counts["positive"] += summary.get("positive", 0)
            sentiment_counts["neutral"] += summary.get("neutral", 0)
            sentiment_counts["negative"] += summary.get("negative", 0)
            
            # 获取每条微博对应的情感结果
            analyses = response_data.get("analyses", [])
            # 检查 analyses 数量是否与当前 chunk 数量一致
            if len(analyses) != len(chunk):
                print("警告：分析结果数量与原始数据数量不匹配！")
            
            # 将每条微博及对应情感写入文件
            with open(output_file, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                for i, row in chunk.iterrows():
                    if i < len(analyses):
                        sentiment = analyses[i].get("sentiment", "")
                    else:
                        sentiment = ""
                    writer.writerow([row["编号"], row["微博正文"], sentiment])
        except json.JSONDecodeError as e:
            print("JSON解析失败:", e)

    print("累计情感统计:")
    print("Positive:", sentiment_counts["positive"])
    print("Neutral:", sentiment_counts["neutral"])
    print("Negative:", sentiment_counts["negative"])
    return sentiment_counts, output_file

def perform_topic_analysis(csv_file: str):
    """
    读取 CSV 文件，分批调用 TopicModellingAgent 进行主题分析，
    并根据返回结果更新主题列表和统计每个主题的讨论量，同时将每条公民意见及对应的主题写入 "topic_modelling_output.csv" 文件。
    返回更新后的主题列表和统计字典。
    """
    initial_topics = []
    df = pd.read_csv(csv_file, encoding='utf-8')
    chunk_size = 10
    num_rows = len(df)
    topics = initial_topics.copy()  # 初始化主题列表
    topic_counts = {}  # 初始化每个主题的讨论量统计

    output_file = "topic_modelling_output.csv"
    # 检查文件是否存在，若不存在则创建并写入表头
    if not os.path.exists(output_file):
        with open(output_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["编号", "微博正文", "topics"])

    for start in tqdm(range(0, num_rows, chunk_size), desc="Processing chunks"):
        # 每个批次重新实例化 agent，避免对话历史过长
        agent = TopicModellingAgent("./prompts/Topic_modelling_prompt.txt")
        
        # 取出当前块数据，并为每条数据添加编号
        chunk = df.iloc[start:start + chunk_size].copy()
        chunk.reset_index(drop=True, inplace=True)
        chunk['编号'] = chunk.index + 1
        
        # 拼接每条公民意见数据（假设 CSV 中的“微博正文”列包含公民意见）
        query_lines = chunk.apply(lambda row: f"{row['编号']}: {row['微博正文']}", axis=1)
        opinions_text = "\n".join(query_lines)
        
        # 构造 query：包含当前批次的公民意见和已确定的主题列表
        topics_str = ", ".join(topics) if topics else "无"
        query = (
            f"请基于以下公民意见数据和当前主题列表进行主题分析：\n\n"
            f"公民意见：\n{opinions_text}\n\n"
            f"当前主题列表：{topics_str}\n\n"
        )
        
        response_str = agent.run(query)
        cleaned_response = clean_json_output(response_str)
        print(cleaned_response)
        
        try:
            response_data = json.loads(cleaned_response)
            analyses = response_data.get("analyses", [])
            # 将每条公民意见及对应的主题写入文件
            with open(output_file, "a", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                if len(analyses) != len(chunk):
                    print("警告：分析结果数量与原始数据数量不匹配！")
                for i, row in chunk.iterrows():
                    if i < len(analyses):
                        topics_list = analyses[i].get("topics", [])
                        topics_output = ", ".join(topic.strip() for topic in topics_list if topic.strip())
                    else:
                        topics_output = ""
                    writer.writerow([row["编号"], row["微博正文"], topics_output])
            
            # 更新主题列表和讨论量统计
            for item in analyses:
                topics_list = item.get("topics", [])
                for topic in topics_list:
                    topic = topic.strip()
                    if topic:
                        if topic not in topics:
                            topics.append(topic)
                            print("新增主题：", topic)
                        if topic in topic_counts:
                            topic_counts[topic] += 1
                        else:
                            topic_counts[topic] = 1
        except json.JSONDecodeError as e:
            print("JSON解析失败:", e)

    print("更新后的主题列表:")
    print(topics)
    print("每个主题的讨论量:")
    print(topic_counts)
    return topic_counts, output_file

def summarize_sentiment_event(event_keywords, sentiment_counts):
    """
    根据事件关键字和累积情感统计生成总结的 prompt，
    并调用 Summarizer agent 返回清洗后的事件总结。
    
    参数:
        event_keywords: 事件关键字列表（例如 ["#金价上涨#"]，取第一个关键字）
        sentiment_counts: 累积情感统计字典，包含 "positive", "neutral", "negative"
        
    返回:
        Summarizer 生成的事件总结文本（清洗后的结果）
    """
    if isinstance(event_keywords, list):
        event_keyword = event_keywords[0]
    else:
        event_keyword = event_keywords

    prompt = (
        f"请帮我对 {event_keyword} 事件进行总结，它的累计情感统计:\n"
        f"Positive: {sentiment_counts['positive']}\n"
        f"Neutral: {sentiment_counts['neutral']}\n"
        f"Negative: {sentiment_counts['negative']}"
    )
    print(prompt)
    summarizer = Summarizer("./prompts/Summarizer_sentiment.txt")
    summarizer_response = summarizer.run(prompt)
    cleaned_summary_response = clean_json_output(summarizer_response)
    
    return cleaned_summary_response

def summarize_topic_event(event_keywords, topic_counts):
    """
    根据事件关键字和主题讨论量生成总结的 prompt，
    并调用 Summarizer agent 返回清洗后的事件总结。

    参数:
        event_keywords: 事件关键字列表（例如 ["#深圳疫情#"]，取第一个关键字）
        topic_counts: 累积主题讨论量统计字典，例如:
                      {'深圳市民对疫情的不满情绪': 7, '深圳疫情防控措施': 12, ...}
        
    返回:
        Summarizer 生成的事件总结文本（清洗后的结果）
    """
    # 取出事件关键字（若为列表则取第一个）
    if isinstance(event_keywords, list):
        event_keyword = event_keywords[0]
    else:
        event_keyword = event_keywords

    # 构造主题统计部分的文本，每行格式为 "主题: 讨论量"
    topics_str = ""
    for topic, count in topic_counts.items():
        topics_str += f"{topic}: {count}\n"

    prompt = (
        f"请帮我对 {event_keyword} 事件进行总结，以下是各主题的讨论量统计：\n"
        f"{topics_str}"
    )
    print(prompt)
    
    # 使用 Summarizer agent（系统提示路径为 "./prompts/Summarizer_topic_sentiment.txt"）
    summarizer = Summarizer("./prompts/Summarizer_topic.txt")
    summarizer_response = summarizer.run(prompt)
    cleaned_summary_response = clean_json_output(summarizer_response)
    
    return cleaned_summary_response

def summarize_event(event_keyword, sentiment_summary=None, topic_summary=None, merged_analysis=None):
    """
    合并情感分析总结、主题分析总结以及合并统计信息，并生成最终事件总结。

    参数:
        event_keyword: 事件关键字（例如 "#深圳疫情#"）
        sentiment_summary: 情感分析生成的总结文本（字符串，可为 None）
        topic_summary: 主题分析生成的总结文本（字符串，可为 None）
        merged_analysis: 合并统计信息，可以是包含 topics 对应 sentiment 数量统计的 DataFrame 或字符串

    返回:
        Summarizer agent 生成的最终事件总结文本（清洗后的结果）
    """
    # 将 merged_analysis 转换为字符串（如果它是 DataFrame）
    if merged_analysis is not None:
        if hasattr(merged_analysis, 'to_string'):
            merged_analysis_str = merged_analysis.to_string()
        else:
            merged_analysis_str = str(merged_analysis)
    else:
        merged_analysis_str = "无"
    
    sentiment_text = sentiment_summary if sentiment_summary is not None else "无"
    topic_text = topic_summary if topic_summary is not None else "无"
    
    prompt = (
        f"请帮我对 {event_keyword} 事件进行总结，综合以下三部分信息：\n\n"
        f"【情感分析总结】:\n{sentiment_text}\n\n"
        f"【主题分析总结】:\n{topic_text}\n\n"
        f"【合并统计信息】:\n{merged_analysis_str}\n\n"
        "请生成最终的事件总结。"
    )
    print(prompt)
    
    summarizer = Summarizer("./prompts/Summarizer_topic.txt")
    summarizer_response = summarizer.run(prompt)
    cleaned_summary_response = clean_json_output(summarizer_response)
    
    return cleaned_summary_response

