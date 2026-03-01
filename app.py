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
        # 月供计算
        if self.i_loan == 0:
            self.M = self.L / self.n
        else:
            self.M = self.L * self.i_loan * (1 + self.i_loan) ** self.n / ((1 + self.i_loan) ** self.n - 1)

        # 资金分配
        self.cash_locked = self.P_down + self.P_car
        self.cash_remaining = self.A - self.cash_locked

        # 月收益
        self.income_total = self.A * self.i_invest
        self.income_remaining = self.cash_remaining * self.i_invest

        # 净成本
        self.net_cost_buy = self.M - self.income_remaining
        self.net_cost_rent = self.R_rent - self.income_total

        # 主权溢价 & 安全边际
        self.delta_p = self.net_cost_buy - self.net_cost_rent
        self.safety_margin = self.S_save - self.M

        # 30年动态模拟
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
st.markdown("量化买房 vs 租房的真实成本，考虑资金机会成本与长期财富积累")

# 侧边栏参数
st.sidebar.header("📋 参数配置")

# 使用列布局让输入更紧凑
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

# 计算按钮
if st.sidebar.button("🚀 开始计算", type="primary", use_container_width=True):
    # 参数校验
    if down_payment + car_cost > total_cash:
        st.error("❌ 首付+购车款不能超过初始现金！")
    else:
        # 计算
        model = HousingSovereigntyModel(
            total_cash, house_price, down_payment, car_cost,
            loan_rate, int(loan_years), invest_rate, rent, savings
        )
        model.calculate()

        # 保存到 session
        st.session_state.model = model
        st.session_state.calculated = True

# ==================== 结果展示 ====================
if st.session_state.get('calculated'):
    model = st.session_state.model

    # 关键指标卡片
    st.subheader("📊 核心指标")
    c1, c2, c3, c4 = st.columns(4)

    delta_color = "inverse" if model.delta_p > 0 else "normal"
    c1.metric("主权溢价 (ΔP)", f"{model.delta_p:,.0f} 元/月",
              delta=f"买房多付{model.delta_p:,.0f}" if model.delta_p > 0 else f"买房省{abs(model.delta_p):,.0f}",
              delta_color=delta_color)

    safety_color = "normal" if model.safety_margin > 0 else "off"
    c2.metric("安全边际", f"{model.safety_margin:,.0f} 元/月",
              delta="安全" if model.safety_margin > 0 else "危险",
              delta_color=safety_color)

    xt5 = model.delta_p * 12 * 30 / 300000
    c3.metric("30年溢价", f"{xt5:.1f} 台XT5", delta=f"≈{xt5 * 30:.0f}万")

    wealth_diff = model.wealth_diff / 10000
    c4.metric("30年财富差", f"{wealth_diff:,.1f} 万",
              delta=f"买房多{wealth_diff:.1f}万" if wealth_diff > 0 else f"租房多{abs(wealth_diff):.1f}万",
              delta_color="normal" if wealth_diff > 0 else "inverse")

    st.markdown("---")

    # 详细分析
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("💰 首月现金流对比")
        st.write(f"**买房方案：**")
        st.write(f"- 月供支出：{model.M:,.0f} 元")
        st.write(f"- 剩余资金收益：{model.income_remaining:,.0f} 元/月")
        st.write(f"- **净月成本：{model.net_cost_buy:,.0f} 元**")
        st.write(f"- 剩余现金：{model.cash_remaining / 10000:.1f} 万")

        st.write(f"**租房方案：**")
        st.write(f"- 租金支出：{model.R_rent:,.0f} 元")
        st.write(f"- 全部资金收益：{model.income_total:,.0f} 元/月")
        st.write(f"- **净月成本：{model.net_cost_rent:,.0f} 元**")

    with col_right:
        st.subheader("📈 30年动态模拟结果")

        chart_data = pd.DataFrame({
            "方案": ["买房(含房产)", "纯租房"],
            "期末资产(万)": [model.final_balance_buy / 10000, model.final_balance_rent / 10000]
        })

        chart_data["颜色"] = ["买房", "租房"]  # 添加颜色分组列
        st.bar_chart(chart_data, x="方案", y="期末资产(万)", color="颜色")

        st.info(f"""
        **注意：** 买房方案的 {model.final_balance_buy / 10000:.1f}万 **不包含房产本身价值**。
        若考虑房产，实际财富应为 {model.final_balance_buy / 10000 + model.house_price / 10000:.1f}万。
        """)

    # 决策建议
    st.markdown("---")
    st.subheader("💡 决策建议")

    if model.delta_p > 0 and model.wealth_diff > 0:
        st.success(f"""
        **买房更优！** 虽然每月多付 {model.delta_p:.0f} 元主权溢价，
        但30年后财富多积累 {model.wealth_diff / 10000:.1f} 万。
        房子既是居住主权，也是强制储蓄工具。
        """)
    elif model.delta_p < 0:
        st.success(f"""
        **存在套利空间！** 买房每月比租房省 {abs(model.delta_p):.0f} 元，
        建议立即买房，这是难得的划算时机。
        """)
    else:
        st.warning(f"""
        **租房更灵活！** 买房每月多付 {model.delta_p:.0f} 元，
        且30年后财富少 {abs(model.wealth_diff) / 10000:.1f} 万。
        建议继续租房，资金用于理财或投资更高收益标的。
        """)

else:
    st.info("👈 请在左侧配置参数并点击「开始计算」")
