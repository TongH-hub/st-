# # -*- coding: utf-8 -*-
# """
# Created on Wed Mar 19 13:56:50 2025

# @author: 35831
# """


import pybroker
from pybroker.ext.data import AKShare
from pybroker import ExecContext, StrategyConfig, Strategy
from pybroker.ext.data import AKShare
import matplotlib.pyplot as plt
import pandas as pd
import riskfolio as rp
import streamlit as st
import numpy as np
#正常显示画图时出现的中文和负号
from pylab import mpl
import quantstats as qs
mpl.rcParams['font.sans-serif']=['SimHei']
mpl.rcParams['axes.unicode_minus']=False
akshare = AKShare()
pybroker.enable_data_source_cache('akshare')
import akshare as ak
# 获取A股行业板块名称数据
stock_board_industry_name_em_df = ak.stock_board_industry_name_em()
option1=st.selectbox(
    "The Industry of your choice",
    stock_board_industry_name_em_df['板块名称'].values.tolist()
    )
# 添加单行文本输入框
#########默认日期
# 添加文本输入框，设置默认值
default_start_date = "1/1/2023"  # 默认开始日期
default_end_date = "12/31/2023"    # 默认结束日期
start_time = st.text_input(
    "请输入开始日期(格式为mm/dd/yyyy, 月/日/年)：",
    value=default_start_date,  # 默认值
    placeholder="例如：1/1/2023"
)

end_time = st.text_input(
    "请输入结束日期(格式为mm/dd/yyyy, 月/日/年)：",
    value=default_end_date,  # 默认值
    placeholder="例如：12/31/2023"
)

stock_board_industry_cons_em_df = ak.stock_board_industry_cons_em(symbol=option1)
stock_qiche=stock_board_industry_cons_em_df.sort_values(by="市盈率-动态", ascending=False)

df = akshare.query(
    symbols=stock_qiche["代码"].values,
    start_date=start_time,
    end_date=end_time,
    timeframe="1d",
    )

df_qiche = df.merge(stock_qiche[["代码","名称"]],left_on="symbol",right_on="代码",how="left")
stock_close=df_qiche.pivot(index="date",columns="名称",values="close").bfill().ffill()
Y_all=stock_close.pct_change().dropna()
stock_close_div0=stock_close.div(stock_close.iloc[0,:],axis=1)
fig=plt.figure(figsize=(18,6))
st.line_chart(stock_close_div0)



##############资产配置
Y = Y_all
method_mu='hist'  # 基于历史数据估计预期收益率的方法
method_cov='hist'  # 基于历史数据估计协方差矩阵的方法
port = rp.Portfolio(returns=Y)
port.assets_stats(method_mu=method_mu, method_cov=method_cov)

default_min_weight = 0.01  # 1%
default_max_weight = 0.3  # 30%
# min_weight = st.text_input(
#     "单个股票资产投资比例最小为",
#     value=default_min_weight,  # 默认值
#     placeholder=0.01
# )
min_weight = st.number_input(
    "单个股票资产投资比例最小为(输入0.01的整数倍)",
    value=default_min_weight,  # 默认值
    min_value=0.0,  # 最小值
    max_value=1.0,  # 最大值
    step=0.01,  # 步长
    format="%.2f"  # 显示格式，保留两位小数
)

max_weight = st.number_input(
    "单个股票资产投资比例最大为(输入0.01的整数倍)",
    value=default_max_weight,  # 默认值
    min_value=0.0,  # 最小值
    max_value=1.0,  # 最大值
    step=0.01,  # 步长
    format="%.2f"  # 显示格式，保留两位小数
)

Ainequality = np.vstack([-np.eye(len(stock_qiche)), np.eye(len(stock_qiche))])  # 合并最小和最大权重约束
binequality = np.hstack([-np.array([min_weight] * len(stock_qiche)), np.array([max_weight] * len(stock_qiche))]).reshape(-1, 1)
model='Classic' 
rm='MSV' 
obj='Sharpe' 
hist = True  
rf=0  
l=0 
# 应用约束条件
port.Ainequality=Ainequality
port.binequality=binequality
port.nea=6
w=port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)
###########设置阈值
threshold=0.01
w.loc[w['weights']<threshold]=0
w.loc[w['weights']!=0]
fig1, ax = plt.subplots(figsize=(10, 8))
rp.plot_drawdown(returns=Y, w=w, alpha=0.05, height=8, width=10, ax=ax)
# 在 Streamlit 中显示绘图
st.pyplot(fig1)
# 计算组合的收益率
# 图1: 月度热力图
portfolio_returns = (Y @ w).dropna()
# 计算月度和年度回报率
monthly_returns = portfolio_returns.resample('M').mean()
annual_returns = portfolio_returns.resample('A').mean()
qs.plots.monthly_heatmap(monthly_returns) 
st.write(qs.stats.monthly_returns(portfolio_returns))


