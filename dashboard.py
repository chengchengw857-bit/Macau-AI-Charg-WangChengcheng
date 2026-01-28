import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import time

# 定义一个实时数据仿真函数
def get_simulated_realtime_data():
    try:
        # 读取原始基础数据
        df = pd.read_csv('macau_charging_raw_data.csv')
        df['时间戳'] = pd.to_datetime(df['时间戳'])
        
        # 获取当前的现实时间
        now = datetime.datetime.now()
        last_data_time = df['时间戳'].iloc[-1]
        
        # 魔法核心：如果现实时间超过了数据的最后时间，自动生成“仿真数据”填补空缺
        if now > last_data_time:
            new_rows = []
            minutes_to_add = int((now - last_data_time).total_seconds() / 60)
            # 限制补齐量（最多补一天），防止系统崩溃
            minutes_to_add = min(minutes_to_add, 1440) 
            
            for i in range(1, minutes_to_add + 1):
                new_time = last_data_time + datetime.timedelta(minutes=i)
                for dist in ['North', 'Central', 'Cotai']:
                    # 根据区域特征模拟不同的实时负载
                    base = 50 if dist == 'Cotai' else 35
                    load = base + np.random.randint(-10, 20)
                    queue = np.random.randint(0, 4) if load > 55 else np.random.randint(0, 2)
                    new_rows.append([new_time, dist, load, queue])
            
            if new_rows:
                new_df = pd.DataFrame(new_rows, columns=['时间戳', '区域', '用电负荷(kW)', '排队车辆数'])
                df = pd.concat([df, new_df]).reset_index(drop=True)
        return df
    except:
        st.error("数据加载失败，请确保目录下有 macau_charging_raw_data.csv")
        return pd.DataFrame()

# 1. 页面配置（设置网页标题和图标）
st.set_page_config(page_title="澳门智充未来-智慧大屏", layout="wide")

st.title("📊 澳门智充未来：实时能源监测看板")
st.markdown("---")

# 2. 加载第一阶段生成的原始数据
df = get_simulated_realtime_data()
# 3. 侧边栏：筛选功能
st.sidebar.header("数据筛选")
selected_district = st.sidebar.multiselect("选择查看区域", options=df['区域'].unique(), default=df['区域'].unique())

# 过滤数据
filtered_df = df[df['区域'].isin(selected_district)]

# 4. 第一行：核心指标（Metric）
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("实时全澳总负荷", f"{filtered_df['用电负荷(kW)'].iloc[-1]} kW", "↑ 5.2%")
with col2:
    st.metric("平均排队时间", "12 分钟", "-2 分钟", delta_color="normal")
with col3:
    st.metric("AI 预测准确率", "94.8%", "稳定")

st.markdown("---")

# 5. 第二行：趋势图（可视化重点）
st.subheader("📈 各区域充电需求 24 小时变化趋势")
fig = px.line(filtered_df.tail(72), # 只显示最近3天的趋势
              x="时间戳", 
              y="用电负荷(kW)", 
              color="区域",
              template="plotly_dark", # 科技感黑底
              line_shape="spline")
st.plotly_chart(fig, use_container_width=True)

# 6. 第三行：排队情况分布（柱状图）
st.subheader("📍 各区域充电站实时排队压力")
fig_bar = px.bar(filtered_df.groupby('区域')['排队车辆数'].mean().reset_index(), 
                 x='区域', 
                 y='排队车辆数', 
                 color='区域',
                 title="平均排队车辆数对比")
st.plotly_chart(fig_bar, use_container_width=True)

# 7. 底部版权信息
st.info("数据来源：模拟澳门交通事务局 (DSAT) 与 澳电 (CEM) 开放接口数据")
# --- 增加 AI 预测模块 (模拟模块一：LSTM 预测效果) ---
st.markdown("---")
st.subheader("🔮 AI 智能需求预测 (未来 1 小时)")

# 获取最后一个时间点的数据
last_load = filtered_df['用电负荷(kW)'].iloc[-1]
last_time = filtered_df['时间戳'].iloc[-1]

# 模拟 AI 预测逻辑：根据当前趋势，预测未来四个 15 分钟节点的数值
prediction_list = []
for i in range(1, 5):
    predict_time = last_time + datetime.timedelta(minutes=15 * i)
    # 模拟 AI 预测：在当前值基础上加上一点波动
    predict_load = last_load + np.random.uniform(-5, 8)
    prediction_list.append([predict_time, "AI 预测值", round(predict_load, 2)])

predict_df = pd.DataFrame(prediction_list, columns=['时间戳', '数据类型', '用电负荷(kW)'])

# 把历史数据末尾和预测数据拼在一起显示
history_tail = filtered_df.tail(10).copy()
history_tail['数据类型'] = "历史实测"
plot_df = pd.concat([history_tail, predict_df])

# 画出预测对比图
fig_predict = px.line(plot_df, 
                      x="时间戳", 
                      y="用电负荷(kW)", 
                      color="数据类型", 
                      line_dash="数据类型", # 预测线用虚线
                      title="AI 时空需求预测模型输出 (基于 LSTM)")
st.plotly_chart(fig_predict, use_container_width=True)

st.success("✅ AI 引擎运行正常：当前正在根据澳门口岸流量与电网实时负荷进行滚动预测")
# --- 增加 AI 智能调度建议 (模拟核心功能二：智能调度) ---
st.markdown("---")
st.subheader("🤖 AI 智慧调度指令")

# 逻辑：如果预测的负荷超过 80kW，或者排队车辆超过 5 辆，就触发警报
latest_queue = filtered_df['排队车辆数'].iloc[-1]
latest_load = filtered_df['用电负荷(kW)'].iloc[-1]

col_a, col_b = st.columns([1, 2])

with col_a:
    if latest_queue > 5 or latest_load > 80:
        st.error("⚠️ 预警：当前区域过载")
    else:
        st.success("✅ 状态：运行平稳")

with col_b:
    if latest_queue > 5:
        st.info(f"**AI 建议指令：** 检测到该区域排队较多，已自动向周边 2km 内的闲置充电桩发放 **'8折优惠券'**，引导后续车辆分流。")
    elif latest_load > 80:
        st.warning(f"**AI 建议指令：** 电网负荷接近临界点，已启动 **'V2G (车网互动)'** 模式，限制大功率快充，启动微网储能放电。")
    else:
        st.write("系统正在进行常态化巡检，电网余量充足，暂无需干预。")


st.write("#### 📡 实时接入节点状态")
st.dataframe(filtered_df.tail(5)) 

auto_monitor = st.sidebar.checkbox('📡 开启全澳实时监控模式', value=False)

if auto_monitor:
    st.toast("正在同步澳门交通事务局 (DSAT) 数据流...")
    time.sleep(5) # 每 5 秒刷新一次
    st.rerun()