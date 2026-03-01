import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt

# 设置页面
st.set_page_config(page_title="住房主权量化器", layout="wide", page_icon="🏠")

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


# ==================== 核心模型类 ====================
class HousingSovereigntyModel:
    def __init__(self,
                 total_cash, house_price, down_payment, car_cost,
                 loan_rate_year, loan_years, invest_rate_year, rent_market, monthly_savings):
        self.A = total_cash
        self.house_price = house_price
        self.P_down = down_payment
        self.P_car = car_cost
        self.L = house_price - down_payment
        self.i_loan = loan_rate_year / 100 / 12
        self.n = loan_years * 12
        self.i_invest = invest_rate_year / 100 / 12
        self.R_rent = rent_market
        self.S_save = monthly_savings

    def calculate(self):
        if self.i_loan == 0:
            self.M = self.L / self.n
        else:
            self.M = self.L * self.i_loan * (1 + self.i_loan) ** self.n / ((1 + self.i_loan) ** self.n - 1)

        self.cash_locked = self.P_down + self.P_car
        self.cash_remaining = self.A - self.cash_locked
        self.income_total = self.A * self.i_invest
        self.income_remaining = self.cash_remaining * self.i_invest

        self.net_cost_buy = self.M - self.income_remaining
        self.net_cost_rent = self.R_rent - self.income_total

        self.delta_p = self.net_cost_buy - self.net_cost_rent
        self.safety_margin = self.S_save - self.M
        self.simulate_30_years()

    def simulate_30_years(self):
        balance_buy = self.cash_remaining
        balance_rent = self.A
        for _ in range(self.n):
            balance_buy = balance_buy * (1 + self.i_invest) + self.S_save - self.M
            balance_rent = balance_rent * (1 + self.i_invest) + self.S_save - self.R_rent
        self.final_balance_buy = balance_buy
        self.final_balance_rent = balance_rent
        self.wealth_diff = balance_buy - balance_rent


# ==================== 页面布局 ====================
st.title("🏠 住房主权量化模型 HSM v3.0")

# --- 模型初衷说明 ---
with st.expander("📌 点击展开：为什么我们需要这款量化模型？", expanded=True):
    st.markdown(f"""
    在当代城市生活，尤其是面对大城市的高昂生活成本时，“买房还是租房”早已不是简单的财务选择，而是一场关乎“人生确定性”与“流动性自由”的博弈。

    我们常常焦虑：
    * **到底要不要买房？** 30年的贷款期限是否会锁死我最黄金的青春？
    * **首付该付多少？** 是追求极低月供的安稳，还是保留现金流应对不确定的未来？
    * **车子该买什么档次？** 安全感与消费主义的边界在哪里？

    这款模型诞生的初衷，就是为了将这些感性的焦虑“数字化”。通过解构资金的机会成本，我们将模糊的“归属感”量化为“房产主权价格”。

    **什么是“房产主权价格”？**
    它代表了你为了拥有“自由装修、不被驱赶、资产归属”等权利，每月真实支付的**额外溢价**。它不替你做决定，但它会诚实地告诉你：为了这份“居住主权”，你正在支付多少台“凯迪拉克”的代价，以及你的现金流是否足以支撑这份执念。

    愿数据能帮你拨开迷雾，在生活的精打细算中，找到属于你的那份从容。
    """)

# --- 计算说明说明 ---
with st.expander("📘 点击展开：参数定义与计算逻辑说明"):
    st.markdown("""
    ### 1. 左侧参数详解
    * **初始现金**：你目前手头可以支配的所有现金总额。
    * **首付与车款**：这两项支出被视为“失去流动性”的资金，将不再产生理财收益。
    * **理财年化**：这是衡量“不买房”优势的关键指标，利率越高，不买房的机会成本就越高。
    * **月攒钱能力**：用于评估你在还完房贷后，每个月是“账户在增长”还是“在吃老本”。

    ### 2. 什么是机会成本？
    这是本模型的灵魂。假设你有100万，如果你买了房付了50万首付，那剩下的50万在生钱；如果你没买房，100万都在生钱。
    **这多出来的50万产生的利息，就是你买房的隐形成本。**

    ### 3. 核心指标说明
    * **房产主权价格 (ΔP)**：综合了月供、租金差额以及上述“机会成本”后的真实差值。
    * **30年财富现金差**：模拟30年后，租房者手里的“现金存款”对比买房者手里的“现金存款”多出多少。
    """)

# 侧边栏参数
st.sidebar.header("📋 参数配置")
col1, col2 = st.sidebar.columns(2)
with col1:
    total_cash = st.number_input("初始现金(万)", value=90.0, min_value=0.0) * 10000
    down_payment = st.number_input("首付(万)", value=52.5, min_value=0.0) * 10000
    car_cost = st.number_input("购车款(万)", value=25.0, min_value=0.0) * 10000
    loan_years = st.number_input("贷款年限", value=30, min_value=1, max_value=40)

with col2:
    house_price = st.number_input("房屋总价(万)", value=175.0, min_value=0.0) * 10000
    loan_rate = st.number_input("房贷利率(%)", value=2.6, min_value=0.0, max_value=10.0, step=0.1)
    invest_rate = st.number_input("理财年化(%)", value=3.0, min_value=0.0, max_value=15.0, step=0.1)
    rent = st.number_input("月租金(元)", value=4000, min_value=0)
    savings = st.number_input("月攒钱(元)", value=15000, min_value=0)

if st.sidebar.button("🚀 开始量化主权", type="primary", use_container_width=True):
    if down_payment + car_cost > total_cash:
        st.error("❌ 现金流预警：首付+购车款超过了你的初始初始现金，请调整配置。")
    else:
        model = HousingSovereigntyModel(total_cash, house_price, down_payment, car_cost,
                                        loan_rate, int(loan_years), invest_rate, rent, savings)
        model.calculate()
        st.session_state.model = model
        st.session_state.calculated = True

# ==================== 结果展示 ====================
if st.session_state.get('calculated'):
    model = st.session_state.model

    # 关键指标卡片
    st.subheader("📊 核心量化指标")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("房产主权价格 (ΔP)", f"{model.delta_p:,.0f} 元/月")
        st.caption("为了拥有这套房的“控制权”，你每月比租房多付出的净成本。")

    with c2:
        st.metric("现金流安全边际", f"{model.safety_margin:,.0f} 元/月")
        st.caption("支付月供后，你每月剩余的可支配结余（回血能力）。")

    with c3:
        xt5 = model.delta_p * 12 * 30 / 300000
        st.metric("30年主权代价", f"{xt5:.1f} 台XT5")
        st.caption(f"30年溢价总额约 {model.delta_p * 12 * 30 / 10000:.0f}万。")

    with c4:
        wealth_diff = model.wealth_diff / 10000
        st.metric("30年财富现金差", f"{wealth_diff:,.1f} 万")
        st.caption("30年后，租房方案比买房方案多出（或少出）的现金存款。")

    # 在 c4 指标后面加新的提示框

    # 新增房产价值提示（放在四个指标下面）
    st.markdown("---")
    st.warning(f"""
    ⚠️ **重要提示：上述计算仅包含流动性现金资产，未包含房产本身！**

    实际情况：
    - **买房者30年后拥有**：现金 {model.final_balance_buy / 10000:.1f}万 + **一套使用了30年的房产**
    - **租房者30年后拥有**：现金 {model.final_balance_rent / 10000:.1f}万 + **无房产**

    若考虑房产残值（哪怕按50%折旧约{model.house_price / 20000:.1f}万），买房者实际财富可能更高。

    在当前房地产市场下，房产可能贬值，但很难归零。请根据你对房价走势的判断，综合评估上述结果。
    """)

    st.markdown("---")

    # 详细分析说明
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("💰 成本构成说明")
        with st.container(border=True):
            st.write(f"**房产主权价格详解：**")
            st.write(
                f"1. **机会成本牺牲**：由于首付锁死了现金，你每月损失了约 **{model.income_total - model.income_remaining:,.0f}元** 的理财收益。")
            st.write(f"2. **硬性支出差额**：月供 **{model.M:,.0f}元** 与租金 **{model.R_rent:,.0f}元** 的直接对比。")
            st.write(f"3. **最终核算**：综合利息损失与月供支出，你每月的“主权溢价”为 **{model.delta_p:,.0f}元**。")
            st.info("💡 只要你认为这笔钱买到的“归属感”和“稳定性”超过了其金额本身，买房就是理性的。")

    with col_right:
        st.subheader("📈 财富趋势说明")
        chart_data = pd.DataFrame({
            "方案": ["买房(含房产)", "纯租房"],
            "期末资产(万)": [model.final_balance_buy / 10000, model.final_balance_rent / 10000],
            "颜色": ["买房", "租房"]
        })
        st.bar_chart(chart_data, x="方案", y="期末资产(万)", color="颜色")

        st.write(f"**数据深度解读：**")
        if model.wealth_diff < 0:
            st.write(
                f"⚠️ 在当前利率下，租房的现金流复利效应极强。30年后，纯租房者会比购房者多出 **{abs(model.wealth_diff) / 10000:.1f}万** 现金。")
        else:
            st.write(f"✅ 买房方案在长期中表现更好。虽然支付了主权溢价，但强制储蓄效应让你最终多积累了财富。")

    # 决策建议
    st.markdown("---")
    st.subheader("💡 最终生存策略建议")

    if model.delta_p > 0 and model.wealth_diff > 0:
        st.success(
            f"【最优路径：上车】 虽然每月支付 {model.delta_p:.0f} 元的主权价格，但长远看房产的保值/强制储蓄效应覆盖了成本。")
    elif model.delta_p < 0:
        st.success(f"【绝对套利：立即购买】 买房比租房还便宜！你不仅获得了主权，还省下了现金，属于罕见的财务套利机会。")
    elif abs(model.wealth_diff) / 10000 < 50:
        st.info(
            f"【平衡路径：看个人喜好】 两者财富差距在50万以内。此时财务已不是核心，请根据你对“自由”和“主权”的心理偏好做决定。")
    else:
        st.warning(
            f"【审慎路径：租房为王】 买房的主权价格过高，且30年后现金流亏损巨大。建议保留现金流，用理财收益对冲租金。")

else:
    st.info("👈 请在左侧配置你的存款、房价与未来能力，点击「开始量化主权」查看结果。")
