import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import time

# 1. 页面基础配置：设置为宽屏模式，增加科技感标题
st.set_page_config(page_title="澳门智充未来-实时监控中心", layout="wide", initial_sidebar_state="collapsed")

# --- 核心逻辑：北京时间数据同步与仿真引擎 ---
def get_live_data():
    try:
        # 获取当前北京时间 (针对云服务器UTC时间进行+8处理)
        beijing_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        
        # 读取地基数据
        df = pd.read_csv('macau_charging_raw_data.csv')
        df['时间戳'] = pd.to_datetime(df['时间戳'])
        
        # 获取地基数据中的最后时刻
        last_data_time = df['时间戳'].iloc[-1]
        
        # 如果数据落后于当前北京时间，自动生成实时补丁
        if beijing_now > last_data_time:
            new_rows = []
            # 计算需要补齐的分钟数（为了性能，最多补齐最近12小时）
            gap_minutes = min(int((beijing_now - last_data_time).total_seconds() / 60), 720)
            
            for i in range(1, gap_minutes + 1):
                temp_time = last_data_time + datetime.timedelta(minutes=i)
                for dist in ['North', 'Central', 'Cotai']:
                    # 模拟动态负荷：根据小时判断高峰
                    hour = temp_time.hour
                    base_val = 65 if dist == 'Cotai' else 45
                    peak_factor = 1.7 if 18 <= hour <= 22 else 1.0
                    load_val = base_val * peak_factor + np.random.normal(0, 5)
                    # 模拟排队：负荷越高，排队概率越大
                    queue_val = np.random.randint(4, 9) if load_val > 85 else np.random.randint(0, 3)
                    new_rows.append([temp_time, dist, round(load_val, 2), queue_val])
            
            if new_rows:
                new_df = pd.DataFrame(new_rows, columns=['时间戳', '区域', '用电负荷(kW)', '排队车辆数'])
                df = pd.concat([df, new_df]).reset_index(drop=True)
        
        # 裁剪数据：只显示最近 24 小时，防止网页卡顿
        display_cutoff = beijing_now - datetime.timedelta(hours=24)
        df = df[df['时间戳'] > display_cutoff]
        return df, beijing_now
    except Exception as e:
        st.error(f"系统引擎启动失败: {e}")
        return pd.DataFrame(), datetime.datetime.now()

# 执行数据加载
df, current_time = get_live_data()

# --- 界面展示部分 ---
st.title("🛡️ 澳门智充未来：实时指挥与调度中心")
st.caption(f"🚀 系统已接入 AI 自主运行模式 | 当前北京时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

if not df.empty:
    # 提取当前时刻（最后一条数据）
    latest_ts = df['时间戳'].max()
    latest_snapshot = df[df['时间戳'] == latest_ts]

    # --- 第一行：核心指标跳动 (增加安全检查防止 NaN) ---
    total_kw = latest_snapshot['用电负荷(kW)'].sum() if not latest_snapshot.empty else 0
    raw_avg_queue = latest_snapshot['排队车辆数'].mean() if not latest_snapshot.empty else 0
    
    # 计算排队时间：如果是 NaN 则保底为 5
    safe_avg_queue = raw_avg_queue if pd.notnull(raw_avg_queue) else 0
    wait_time_display = int(safe_avg_queue * 4 + 5)
    
    # 模拟 AI 动态准确率
    ai_acc = 94.5 + np.random.uniform(0, 1.2)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("实时全澳总负荷", f"{round(total_kw, 1)} kW", f"{round(np.random.uniform(-1, 2.5), 1)}%")
    with m2:
        st.metric("AI 预期排队时间", f"{wait_time_display} 分钟", "-1 min")
    with m3:
        st.metric("AI 实时预测准确率", f"{round(ai_acc, 2)}%", "稳定")

    st.markdown("---")

    # --- 第二行：动态可视化图表 ---
    col_l, col_r = st.columns([2, 1])

    with col_l:
        st.subheader("📈 24小时全区负荷滚动监测")
        # 只取最近几百条画图，保证丝滑
        fig_line = px.line(df.tail(600), x="时间戳", y="用电负荷(kW)", color="区域", 
                          template="plotly_dark", line_shape="spline",
                          color_discrete_map={'North':'#FF4B4B', 'Central':'#0068C9', 'Cotai':'#83CFFA'})
        st.plotly_chart(fig_line, use_container_width=True)

    with col_r:
        st.subheader("🚗 各站点当前排队状态")
        fig_bar = px.bar(latest_snapshot, x="区域", y="排队车辆数", color="区域", 
                        text_auto=True, template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- 第三行：AI 智能决策输出 ---
    st.subheader("🤖 AI 实时调度决策建议")
    
    if total_kw > 180 or safe_avg_queue > 5:
        st.error(f"🔴 预警指令：检测到局部站点过载。AI 已自动下发【动态调价】指令：引导后续车辆至路氹区。")
        st.info("💡 系统状态：正在通过 V2G 协议调动周边 50 辆闲置电动车进行微网反向送电...")
    else:
        st.success("🟢 运行报告：全澳能源网络负荷均衡。当前 AI 正在执行全天候自动巡检，无须人工干预。")

    # --- 显示底层数据流 (Demo 必备) ---
    with st.expander("查看底层实时数据流"):
        st.dataframe(df.tail(10), use_container_width=True)

# --- 自动化运行引擎：每 10 秒强制刷新 ---
time.sleep(10)
st.rerun()