import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import numpy as np
import time

# 1. 页面配置 - 工业级宽屏风格
st.set_page_config(page_title=" 澳门智充未来：实时监控与调度中心", layout="wide")

# --- 核心引擎：自愈式实时数据同步器 ---
def get_advanced_data():
    beijing_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    # 扩展维度：负荷、排队、SOH、减碳、换电、绿电比、V2G收益、故障风险
    cols = ['时间戳', '区域', '用电负荷(kW)', '排队车辆数', 'SOH安全指数', '减碳量(kg)', '可用电池数', '绿电比例', 'V2G收益', '故障风险']
    
    try:
        df = pd.read_csv('macau_charging_raw_data.csv', names=cols[:4], header=None)
        df['时间戳'] = pd.to_datetime(df['时间戳'], errors='coerce')
        df = df.dropna(subset=['时间戳'])
        last_time = df['时间戳'].max()
    except:
        last_time = beijing_now - datetime.timedelta(hours=24)
        df = pd.DataFrame(columns=cols[:4])

    if pd.isna(last_time) or (beijing_now - last_time).total_seconds() > 600:
        last_time = beijing_now - datetime.timedelta(hours=24)
        df = pd.DataFrame(columns=cols[:4])

    new_rows = []
    gap_mins = int((beijing_now - last_time).total_seconds() / 60)
    for i in range(1, gap_mins + 1):
        temp_time = last_time + datetime.timedelta(minutes=i)
        for dist in ['North', 'Central', 'Cotai']:
            hour = temp_time.hour
            base = 65 if dist == 'Cotai' else 45
            peak = 1.7 if 18 <= hour <= 22 else 1.0
            load = base * peak + np.random.normal(0, 3)
            queue = np.random.randint(4, 9) if load > 82 else np.random.randint(0, 3)
            
            # 工业指标仿真
            soh = 99.5 - (np.random.random() * 0.2)
            carbon = load * 0.45 
            max_slots = 30
            available_bat = max(0, max_slots - (np.random.randint(8, 15) + (5 if load > 80 else 0)))
            
            # 新增功能模拟数据
            green_energy_pct = 20 + np.random.randint(0, 15) # 绿电比例
            v2g_profit = round(np.random.uniform(2.5, 12.0), 2) if 18 <= hour <= 22 else 0 # V2G收益
            risk_score = round(np.random.uniform(0.1, 1.8), 2) # 故障风险指数

            new_rows.append([temp_time, dist, round(load, 2), queue, round(soh, 2), round(carbon, 2), available_bat, green_energy_pct, v2g_profit, risk_score])
    
    if new_rows:
        new_df = pd.DataFrame(new_rows, columns=cols)
        df = pd.concat([df, new_df]).reset_index(drop=True)
    
    # 缺省字段补全
    for col in ['SOH安全指数', '减碳量(kg)', '可用电池数', '绿电比例', 'V2G收益', '故障风险']:
        if col not in df.columns:
            df[col] = 0

    cutoff = beijing_now - datetime.timedelta(hours=24)
    df = df[df['时间戳'] > cutoff]
    return df, beijing_now

df, current_time = get_advanced_data()

# --- 界面展示 ---
st.title("🔋澳门智充未来：实时监控与调度中心")
st.caption(f"🚀 系统运行等级: **Industrial Grade AI** | 北京时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 第一部分：全栈核心指标看板
latest_data = df[df['时间戳'] == df['时间戳'].max()]
m_row1_1, m_row1_2, m_row1_3, m_row1_4 = st.columns(4)
m_row2_1, m_row2_2, m_row2_3, m_row2_4 = st.columns(4)

with m_row1_1:
    st.metric("全澳实时能源负荷", f"{round(latest_data['用电负荷(kW)'].sum(), 1)} kW", f"{round(np.random.uniform(-1, 2), 1)}%")
with m_row1_2:
    wait_t = int(latest_data['排队车辆数'].mean() * 4 + 5)
    st.metric("AI 预期排队时长", f"{wait_t} 分钟", "-1 min")
with m_row1_3:
    st.metric("累计减碳贡献(ESG)", f"{round(df['减碳量(kg)'].sum(), 1)} kg", "↑ 2.4%")
with m_row1_4:
    st.metric("电池健康监测(SOH)", f"{latest_data['SOH安全指数'].min()}%", "稳定")
with m_row2_1:
    st.metric("换电站可用电池", f"{int(latest_data['可用电池数'].sum())} 组", f"{np.random.randint(-2, 3)} 组")
with m_row2_2:
    st.metric("绿电渗透率(Clean)", f"{int(latest_data['绿电比例'].mean())}%", "↑ 1.5%")
with m_row2_3:
    v2g_total = round(latest_data['V2G收益'].sum(), 2)
    st.metric("V2G 预计实时收益", f"{v2g_total} MOP", "高峰激励", help="基于AI博弈算法计算的车辆反向送电收益")
with m_row2_4:
    st.metric("设备故障风险评级", f"{latest_data['故障风险'].max()}", "低风险", delta_color="inverse")

st.markdown("---")

# 第二部分：核心展示区
tab1, tab2, tab3 = st.tabs(["📊 实时动态大屏", "🧠 AI 深度分析", "🛡️ 智慧调度中枢"])

with tab1:
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.subheader("📈 能源大脑：24小时负荷滚动监测")
        fig = px.line(df, x="时间戳", y="用电负荷(kW)", color="区域", 
                      template="plotly_dark", line_shape="spline",
                      color_discrete_map={'North':'#FF4B4B', 'Central':'#0068C9', 'Cotai':'#83CFFA'})
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        st.subheader("🚗 补能热力分布")
        fig_bar = px.bar(latest_data, x="区域", y="排队车辆数", color="区域", text_auto=True)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.write("---")
        st.subheader("🔋 换电站实时库存")
        fig_bss = px.bar(latest_data, y="区域", x="可用电池数", color="区域", orientation='h', text_auto=True)
        st.plotly_chart(fig_bss, use_container_width=True)

with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🎯 站点 AI 综合评分")
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[90, 85, 95, 80, 88],
            theta=['响应速度','安全性','绿电占比','周转效率','用户评价'],
            fill='toself', name='系统评分'
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), template="plotly_dark")
        st.plotly_chart(fig_radar, use_container_width=True)
    with col_b:
        st.subheader("⚡ 绿电溯源与 V2G 经济性分析")
        # 混合图表：负荷线 + V2G收益柱状图
        fig_mixed = go.Figure()
        fig_mixed.add_trace(go.Scatter(x=df['时间戳'].tail(50), y=df['用电负荷(kW)'].tail(50), name='总负荷', line=dict(color='#00CC96')))
        fig_mixed.add_trace(go.Bar(x=df['时间戳'].tail(50), y=df['V2G收益'].tail(50), name='V2G收益建议', marker_color='#AB63FA'))
        fig_mixed.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig_mixed, use_container_width=True)

with tab3:
    st.subheader("🤖 AI 实时自动调度决策建议")
    
    # 1. 负荷预警
    if latest_data['用电负荷(kW)'].sum() > 185:
        st.error("🔴 **电力负载警告**: 当前电网频率出现波动。AI已启动虚拟电厂(VPP)调度模式。")
    else:
        st.success("🟢 **电力运行报告**: 全澳能源网络稳健。AI正在执行常态化需求侧响应优化。")
    
    # 2. 换电预警
    if latest_data['可用电池数'].min() < 18:
        st.warning(f"🛵 **物流保障**: 监测到局部区域电池库存下降。AI已优化物流补给路径。")
    
    # 3. 故障预测预警
    if latest_data['故障风险'].max() > 1.5:
        st.info("🛠️ **预测性维护**: AI检测到 Node-North-02 散热异常。已自动生成预检工单发至运维端。")
    
    st.write("#### 📡 边缘计算节点实时日志")
    log_df = pd.DataFrame({
        "时间": [current_time.strftime('%H:%M:%S') for _ in range(5)],
        "节点": ["Node-North-01", "Node-Cotai-05", "BSS-Logistics", "V2G-Engine", "Fault-Detector"],
        "任务": ["异常电流监测", "负载均衡计算", "电池库存平衡", "实时套利博弈", "绝缘电阻扫描"],
        "结果": ["Normal", "Optimal", "Syncing", "Calculating", "Healthy"]
    })
    st.table(log_df)

# --- 自动刷新：每10秒同步一次 ---
time.sleep(10)
st.rerun()