#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宜宾市各区县财政与文旅数据分析看板生成脚本
基于公开政府统计数据生成交互式HTML看板和分析报告
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'yibin_data.json')
DASHBOARD_PATH = os.path.join(BASE_DIR, 'dashboard', 'index.html')
REPORT_PATH = os.path.join(BASE_DIR, 'report', 'report.html')
README_PATH = os.path.join(BASE_DIR, 'README.md')


def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def compute_chart_data(data):
    """计算所有图表需要的JSON数据"""
    districts = data['districts']
    years = ['2020', '2021', '2022', '2023', '2024']

    # 全市GDP
    city_gdp_years = years
    city_gdp_vals = []
    for y in years:
        v = data['gdp'].get(y, {}).get('全市')
        city_gdp_vals.append(v if v is not None else None)

    # 各区县GDP时间序列 (用于折线图)
    gdp_series = []
    colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
              '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#ff9f7f']
    for i, d in enumerate(districts):
        vals = []
        for y in years:
            v = data['gdp'].get(y, {}).get(d)
            vals.append(v if v is not None else None)
        gdp_series.append({
            "name": d,
            "type": "line",
            "smooth": True,
            "data": vals,
            "itemStyle": {"color": colors[i % len(colors)]}
        })

    # 2024年GDP排名
    gdp_2024 = {}
    for d in districts:
        v = data['gdp'].get('2024', {}).get(d)
        if v is not None:
            gdp_2024[d] = v
    gdp_2024_sorted = dict(sorted(gdp_2024.items(), key=lambda x: x[1], reverse=True))

    # 2024年财政收入
    rev_2024 = {}
    for d in districts:
        v = data['fiscal_revenue_2024'].get(d)
        if v is not None:
            rev_2024[d] = v
    rev_2024_sorted = dict(sorted(rev_2024.items(), key=lambda x: x[1], reverse=True))

    # 财政自给率
    self_ratio = {}
    for d in districts:
        rev = data['fiscal_revenue_2024'].get(d)
        exp = data['fiscal_expenditure'].get('2023', {}).get(d)
        if rev is not None and exp is not None:
            self_ratio[d] = round(rev / exp * 100, 1)
    self_ratio_sorted = dict(sorted(self_ratio.items(), key=lambda x: x[1], reverse=True))

    # 人均GDP
    pc_gdp = {}
    for d in districts:
        g = data['gdp'].get('2024', {}).get(d)
        p = data['population_2022'].get(d)
        if g is not None and p is not None:
            pc_gdp[d] = round(g * 10000 / p, 0)
    pc_gdp_sorted = dict(sorted(pc_gdp.items(), key=lambda x: x[1], reverse=True))

    # 全市财政
    fis_years = ['2022', '2023', '2024']
    fis_inc = [data['city_fiscal'].get(y, {}).get('收入') for y in fis_years]
    fis_tax = [data['city_fiscal'].get(y, {}).get('税收') for y in fis_years]
    fis_exp = [data['city_fiscal'].get(y, {}).get('支出') for y in fis_years]

    return {
        "city_gdp_years": city_gdp_years,
        "city_gdp_vals": city_gdp_vals,
        "gdp_series": gdp_series,
        "gdp_2024_keys": list(gdp_2024_sorted.keys()),
        "gdp_2024_vals": list(gdp_2024_sorted.values()),
        "rev_2024_keys": list(rev_2024_sorted.keys()),
        "rev_2024_vals": list(rev_2024_sorted.values()),
        "self_ratio_keys": list(self_ratio_sorted.keys()),
        "self_ratio_vals": list(self_ratio_sorted.values()),
        "pc_gdp_keys": list(pc_gdp_sorted.keys()),
        "pc_gdp_vals": list(pc_gdp_sorted.values()),
        "fis_years": fis_years,
        "fis_inc": fis_inc,
        "fis_tax": fis_tax,
        "fis_exp": fis_exp,
    }


def build_table_rows(data):
    """构建HTML表格行"""
    districts = data['districts']
    rows_gdp = []
    rows_fiscal = []
    for d in districts:
        gdp20 = data['gdp'].get('2020', {}).get(d)
        gdp21 = data['gdp'].get('2021', {}).get(d)
        gdp23 = data['gdp'].get('2023', {}).get(d)
        gdp24 = data['gdp'].get('2024', {}).get(d)
        pop = data['population_2022'].get(d)

        def fmt(v):
            return f"{v:.2f}" if isinstance(v, (int, float)) else "-"

        gdp20s = fmt(gdp20)
        gdp21s = fmt(gdp21)
        gdp23s = fmt(gdp23)
        gdp24s = f"<strong>{fmt(gdp24)}</strong>" if gdp24 is not None else "-"
        pops = fmt(pop) if pop is not None else "-"

        growth_html = "-"
        if isinstance(gdp23, (int, float)) and isinstance(gdp24, (int, float)):
            gr = (gdp24 - gdp23) / gdp23 * 100
            cls = "up" if gr > 0 else "down"
            growth_html = f'<span class="kpi-change {cls}">{gr:.1f}%</span>'

        rows_gdp.append(
            f'<tr><td><strong>{d}</strong></td><td class="num">{gdp20s}</td>'
            f'<td class="num">{gdp21s}</td><td class="num">{gdp23s}</td>'
            f'<td class="num">{gdp24s}</td><td class="num">{growth_html}</td>'
            f'<td class="num">{pops}</td></tr>'
        )

        rev = data['fiscal_revenue_2024'].get(d)
        exp = data['fiscal_expenditure'].get('2023', {}).get(d)
        revs = fmt(rev)
        exps = fmt(exp)
        ratio_s = "-"
        if isinstance(rev, (int, float)) and isinstance(exp, (int, float)):
            ratio_s = f"{rev/exp*100:.1f}%"
        pc_s = "-"
        if isinstance(rev, (int, float)) and isinstance(pop, (int, float)):
            pc_s = f"{rev*10000/pop:.0f}"

        rows_fiscal.append(
            f'<tr><td><strong>{d}</strong></td><td class="num">{revs}</td>'
            f'<td class="num">{exps}</td><td class="num">{ratio_s}</td>'
            f'<td class="num">{pc_s}</td></tr>'
        )

    return "\n".join(rows_gdp), "\n".join(rows_fiscal)


def generate_dashboard(data, chart_data, rows_gdp, rows_fiscal):
    """生成交互式数据看板HTML"""
    districts = data['districts']
    scenic_cards = "\n".join(
        f'<div class="scenic-card"><div class="scenic-name">{s["name"]}</div>'
        f'<div class="scenic-meta"><span class="badge badge-primary">{s["level"]}</span>'
        f'<span class="badge badge-success">{s["district"]}</span>'
        f'<span class="badge badge-warning">{s["type"]}</span></div></div>'
        for s in data['scenic_spots']
    )

    # JSON 注入脚本
    chart_json = json.dumps(chart_data, ensure_ascii=False, indent=2)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>宜宾市各区县财政与文旅数据分析看板</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans SC",sans-serif;
  background:#f5f7fa;color:#333;line-height:1.6
}}
.header{{
  background:linear-gradient(135deg,#1a5276 0%,#2980b9 100%);
  color:white;padding:40px 20px;text-align:center
}}
.header h1{{font-size:2.2em;margin-bottom:10px}}
.header p{{opacity:.9;font-size:1.05em}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}
.kpi-row{{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:24px 0
}}
.kpi-card{{
  background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,.06);
  text-align:center;transition:transform .2s
}}
.kpi-card:hover{{transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,.1)}}
.kpi-value{{font-size:2em;font-weight:700;color:#1a5276;margin:8px 0}}
.kpi-label{{color:#666;font-size:.95em}}
.kpi-change{{font-size:.85em;margin-top:4px}}
.kpi-change.up{{color:#27ae60}}
.kpi-change.down{{color:#e74c3c}}
.section{{
  background:white;border-radius:12px;padding:28px;margin:20px 0;box-shadow:0 2px 8px rgba(0,0,0,.06)
}}
.section-title{{
  font-size:1.4em;font-weight:600;color:#1a5276;margin-bottom:20px;
  padding-bottom:12px;border-bottom:2px solid #e8f0f8
}}
.chart-container{{width:100%;height:420px;margin:16px 0}}
.chart-grid{{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:20px
}}
.chart-grid .section{{margin:0}}
.data-table{{
  width:100%;border-collapse:collapse;margin-top:12px;font-size:.95em
}}
.data-table th,.data-table td{{
  padding:12px 16px;text-align:left;border-bottom:1px solid #eee
}}
.data-table th{{
  background:#f8f9fa;font-weight:600;color:#555;position:sticky;top:0
}}
.data-table tr:hover{{background:#f8f9fa}}
.data-table td.num{{text-align:right;font-family:monospace}}
.badge{{
  display:inline-block;padding:2px 10px;border-radius:12px;font-size:.8em;font-weight:500
}}
.badge-primary{{background:#e8f0f8;color:#1a5276}}
.badge-success{{background:#e8f8f0;color:#27ae60}}
.badge-warning{{background:#fff8e8;color:#f39c12}}
.tabs{{
  display:flex;gap:8px;margin-bottom:20px;border-bottom:2px solid #eee;padding-bottom:8px
}}
.tab{{
  padding:8px 20px;border-radius:6px;cursor:pointer;font-weight:500;
  transition:all .2s;border:none;background:transparent;color:#666
}}
.tab:hover{{background:#f0f0f0}}
.tab.active{{background:#1a5276;color:white}}
.tab-content{{display:none}}
.tab-content.active{{display:block}}
.footer{{
  text-align:center;padding:40px 20px;color:#999;font-size:.9em
}}
.scenic-grid{{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-top:16px
}}
.scenic-card{{
  background:linear-gradient(135deg,#f8f9fa 0%,#fff 100%);
  border:1px solid #e8e8e8;border-radius:10px;padding:20px;transition:all .2s
}}
.scenic-card:hover{{border-color:#2980b9;box-shadow:0 4px 12px rgba(41,128,185,.1)}}
.scenic-name{{font-weight:600;color:#1a5276;font-size:1.1em}}
.scenic-meta{{color:#888;font-size:.9em;margin-top:6px}}
@media(max-width:768px){{
  .header h1{{font-size:1.5em}}
  .chart-grid{{grid-template-columns:1fr}}
  .chart-container{{height:320px}}
}}
</style>
</head>
<body>
<div class="header">
  <h1>宜宾市各区县财政与文旅数据分析看板</h1>
  <p>基于 2021-2025 年公开政府统计数据 | 数据驱动决策</p>
</div>

<div class="container">
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-label">2024年全市GDP</div>
      <div class="kpi-value">4005.8<span style="font-size:.5em">亿元</span></div>
      <div class="kpi-change up">四川省第3位</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">2024年财政收入</div>
      <div class="kpi-value">324.3<span style="font-size:.5em">亿元</span></div>
      <div class="kpi-change up">全省第2位 · 增长3.3%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">2024年接待游客</div>
      <div class="kpi-value">9738<span style="font-size:.5em">万人次</span></div>
      <div class="kpi-change up">旅游收入 898亿元</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">A级景区数量</div>
      <div class="kpi-value">55<span style="font-size:.5em">家</span></div>
      <div class="kpi-change up">含6家4A级景区</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">全市GDP发展趋势（2020-2024）</div>
    <div id="chart-city-gdp" class="chart-container"></div>
  </div>

  <div class="chart-grid">
    <div class="section">
      <div class="section-title">2024年各区县GDP排名</div>
      <div id="chart-gdp-2024" class="chart-container"></div>
    </div>
    <div class="section">
      <div class="section-title">2024年各区县财政收入排名</div>
      <div id="chart-fiscal-2024" class="chart-container"></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">各区县GDP变化趋势（2020-2024）</div>
    <div id="chart-gdp-trend" class="chart-container"></div>
  </div>

  <div class="chart-grid">
    <div class="section">
      <div class="section-title">2024年财政自给率（收入/2023年支出）</div>
      <div id="chart-self-ratio" class="chart-container"></div>
    </div>
    <div class="section">
      <div class="section-title">2024年人均GDP估算（元/人）</div>
      <div id="chart-pc-gdp" class="chart-container"></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">全市财政收入与支出趋势</div>
    <div id="chart-city-fiscal" class="chart-container"></div>
  </div>

  <div class="section">
    <div class="section-title">交互式数据总表</div>
    <div class="tabs">
      <button class="tab active" onclick="switchTab(event,'tab-gdp')">GDP数据</button>
      <button class="tab" onclick="switchTab(event,'tab-fiscal')">财政数据</button>
      <button class="tab" onclick="switchTab(event,'tab-tourism')">文旅资源</button>
    </div>
    <div id="tab-gdp" class="tab-content active">
      <table class="data-table">
        <thead><tr><th>区县</th><th>2020年GDP(亿元)</th><th>2021年GDP(亿元)</th><th>2023年GDP(亿元)</th><th>2024年GDP(亿元)</th><th>2024年增速</th><th>人口(万人)</th></tr></thead>
        <tbody>
{rows_gdp}
        </tbody>
      </table>
    </div>
    <div id="tab-fiscal" class="tab-content">
      <table class="data-table">
        <thead><tr><th>区县</th><th>2024年收入(亿元)</th><th>2023年支出(亿元)</th><th>财政自给率</th><th>人均财力(元/人)</th></tr></thead>
        <tbody>
{rows_fiscal}
        </tbody>
      </table>
    </div>
    <div id="tab-tourism" class="tab-content">
      <div class="scenic-grid">
{scenic_cards}
      </div>
      <div style="margin-top:24px">
        <h4 style="color:#1a5276;margin-bottom:12px">2024年全市文旅概览</h4>
        <table class="data-table">
          <thead><tr><th>指标</th><th>数值</th></tr></thead>
          <tbody>
            <tr><td>游客接待量</td><td class="num">9738万人次</td></tr>
            <tr><td>旅游总收入</td><td class="num">898亿元</td></tr>
            <tr><td>A级景区数量</td><td class="num">55家</td></tr>
            <tr><td>4A级景区</td><td class="num">6家</td></tr>
            <tr><td>旅游收入占GDP比重</td><td class="num">22.4%</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<div class="footer">
  <p>数据来源：宜宾市统计局、财政局、文旅局公开数据 | 更新时间：2025年7月</p>
  <p>注：部分年份区县级数据因公开渠道限制暂未获取，以"-"标注</p>
</div>

<script>
const CHART_DATA = {chart_json};

function switchTab(ev, tabId) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  ev.target.classList.add('active');
}}

// 全市GDP趋势
const chartCityGdp = echarts.init(document.getElementById('chart-city-gdp'));
chartCityGdp.setOption({{
  tooltip: {{ trigger: 'axis' }},
  xAxis: {{ type: 'category', data: CHART_DATA.city_gdp_years, axisLabel: {{ fontSize: 13 }} }},
  yAxis: {{ type: 'value', name: '亿元', axisLabel: {{ fontSize: 12 }} }},
  series: [{{
    data: CHART_DATA.city_gdp_vals,
    type: 'line', smooth: true, symbolSize: 10,
    lineStyle: {{ width: 3, color: '#1a5276' }},
    itemStyle: {{ color: '#1a5276' }},
    areaStyle: {{
      color: new echarts.graphic.LinearGradient(0,0,0,1,[
        {{ offset:0, color:'rgba(26,82,118,0.3)' }},
        {{ offset:1, color:'rgba(26,82,118,0.05)' }}
      ])
    }},
    label: {{ show: true, position: 'top', fontSize: 13, fontWeight: 'bold' }}
  }}]
}});

// 2024年各区县GDP
const chartGdp2024 = echarts.init(document.getElementById('chart-gdp-2024'));
chartGdp2024.setOption({{
  tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
  xAxis: {{ type: 'category', data: CHART_DATA.gdp_2024_keys, axisLabel: {{ fontSize: 12, rotate: 30 }} }},
  yAxis: {{ type: 'value', name: '亿元' }},
  series: [{{
    data: CHART_DATA.gdp_2024_vals,
    type: 'bar', barWidth: '55%',
    itemStyle: {{
      color: new echarts.graphic.LinearGradient(0,0,0,1,[
        {{ offset:0, color:'#2980b9' }},
        {{ offset:1, color:'#1a5276' }}
      ])
    }},
    label: {{ show: true, position: 'top', fontSize: 11 }}
  }}]
}});

// 2024年财政收入
const chartFiscal2024 = echarts.init(document.getElementById('chart-fiscal-2024'));
chartFiscal2024.setOption({{
  tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
  xAxis: {{ type: 'category', data: CHART_DATA.rev_2024_keys, axisLabel: {{ fontSize: 12, rotate: 30 }} }},
  yAxis: {{ type: 'value', name: '亿元' }},
  series: [{{
    data: CHART_DATA.rev_2024_vals,
    type: 'bar', barWidth: '55%',
    itemStyle: {{ color: '#27ae60' }},
    label: {{ show: true, position: 'top', fontSize: 11 }}
  }}]
}});

// GDP趋势对比
const chartGdpTrend = echarts.init(document.getElementById('chart-gdp-trend'));
chartGdpTrend.setOption({{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: {json.dumps(districts, ensure_ascii=False)}, top: 0, textStyle: {{ fontSize: 11 }} }},
  xAxis: {{ type: 'category', data: CHART_DATA.city_gdp_years }},
  yAxis: {{ type: 'value', name: '亿元' }},
  series: CHART_DATA.gdp_series
}});

// 财政自给率
const chartSelfRatio = echarts.init(document.getElementById('chart-self-ratio'));
chartSelfRatio.setOption({{
  tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }}, formatter: '{{b}}: {{c}}%' }},
  xAxis: {{ type: 'category', data: CHART_DATA.self_ratio_keys, axisLabel: {{ fontSize: 12, rotate: 30 }} }},
  yAxis: {{ type: 'value', name: '%', max: 100 }},
  series: [{{
    data: CHART_DATA.self_ratio_vals,
    type: 'bar', barWidth: '55%',
    itemStyle: {{
      color: function(params) {{
        const colors = ['#27ae60','#2ecc71','#f1c40f','#e67e22','#e74c3c','#c0392b','#8e44ad','#9b59b6','#3498db','#2980b9'];
        return colors[params.dataIndex % colors.length];
      }}
    }},
    label: {{ show: true, position: 'top', formatter: '{{c}}%', fontSize: 11 }}
  }}]
}});

// 人均GDP
const chartPcGdp = echarts.init(document.getElementById('chart-pc-gdp'));
chartPcGdp.setOption({{
  tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
  xAxis: {{ type: 'category', data: CHART_DATA.pc_gdp_keys, axisLabel: {{ fontSize: 12, rotate: 30 }} }},
  yAxis: {{ type: 'value', name: '元/人' }},
  series: [{{
    data: CHART_DATA.pc_gdp_vals,
    type: 'bar', barWidth: '55%',
    itemStyle: {{ color: '#9b59b6' }},
    label: {{ show: true, position: 'top', formatter: function(p){{ return (p.value/10000).toFixed(1)+'万'; }}, fontSize: 11 }}
  }}]
}});

// 全市财政趋势
const chartCityFiscal = echarts.init(document.getElementById('chart-city-fiscal'));
chartCityFiscal.setOption({{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: ['财政收入','税收收入','财政支出'], top: 0 }},
  xAxis: {{ type: 'category', data: CHART_DATA.fis_years }},
  yAxis: {{ type: 'value', name: '亿元' }},
  series: [
    {{ name: '财政收入', type: 'bar', data: CHART_DATA.fis_inc, itemStyle: {{ color: '#2980b9' }}, barWidth: '25%' }},
    {{ name: '税收收入', type: 'bar', data: CHART_DATA.fis_tax, itemStyle: {{ color: '#27ae60' }}, barWidth: '25%' }},
    {{ name: '财政支出', type: 'bar', data: CHART_DATA.fis_exp, itemStyle: {{ color: '#e74c3c' }}, barWidth: '25%' }}
  ]
}});

window.addEventListener('resize', function() {{
  chartCityGdp.resize(); chartGdp2024.resize(); chartFiscal2024.resize();
  chartGdpTrend.resize(); chartSelfRatio.resize(); chartPcGdp.resize(); chartCityFiscal.resize();
}});
</script>
</body>
</html>
'''
    return html


def generate_report(data):
    """生成分析报告HTML"""
    districts = data['districts']

    # 财政自给率表格
    fiscal_rows = []
    for d in districts:
        rev = data['fiscal_revenue_2024'].get(d)
        exp = data['fiscal_expenditure'].get('2023', {}).get(d)
        if rev is not None and exp is not None:
            ratio = rev / exp * 100
            if ratio >= 50:
                ev = "自给能力较强"
            elif ratio >= 30:
                ev = "自给能力一般，依赖转移支付"
            else:
                ev = "自给能力弱，高度依赖转移支付"
            fiscal_rows.append(
                f'<tr><td>{d}</td><td class="num">{rev:.2f}</td>'
                f'<td class="num">{exp:.2f}</td><td class="num">{ratio:.1f}%</td>'
                f'<td>{ev}</td></tr>'
            )

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>宜宾市各区县财政与文旅发展分析报告</title>
<style>
body{{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans SC",sans-serif;
  max-width:900px;margin:0 auto;padding:40px 20px;line-height:1.8;color:#333;background:#fafafa
}}
h1{{color:#1a5276;text-align:center;border-bottom:3px solid #1a5276;padding-bottom:16px}}
h2{{color:#1a5276;margin-top:36px;border-left:4px solid #2980b9;padding-left:12px}}
h3{{color:#555;margin-top:24px}}
.meta{{text-align:center;color:#888;margin:16px 0 32px;font-size:.95em}}
.highlight{{background:#fff3cd;padding:2px 6px;border-radius:4px}}
.insight-box{{
  background:linear-gradient(135deg,#e8f0f8 0%,#f0f7ff 100%);
  border-left:4px solid #2980b9;padding:20px;margin:20px 0;border-radius:0 8px 8px 0
}}
.warning-box{{
  background:linear-gradient(135deg,#fff8e8 0%,#fffbf0 100%);
  border-left:4px solid #f39c12;padding:20px;margin:20px 0;border-radius:0 8px 8px 0
}}
table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:.95em;background:white}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #e0e0e0}}
th{{background:#f0f4f8;font-weight:600;color:#555}}
tr:hover{{background:#f8f9fa}}
td.num{{text-align:right;font-family:monospace}}
.footer{{margin-top:60px;padding-top:20px;border-top:1px solid #e0e0e0;color:#999;font-size:.9em;text-align:center}}
</style>
</head>
<body>
<h1>宜宾市各区县财政与文旅发展分析报告</h1>
<div class="meta">数据周期：2021-2025年 | 报告日期：2025年7月 | 数据来源：公开政府统计</div>

<h2>一、概述</h2>
<p>宜宾市位于四川省南部，地处川、滇、黔三省结合部，是长江上游区域中心城市。全市辖3区7县，总面积约1.33万平方公里，2024年末常住人口约461万人。</p>
<p>2024年，宜宾市实现地区生产总值<span class="highlight">4005.76亿元</span>，经济总量排名四川省第三位；一般公共预算收入324.3亿元，排名全省第二位。同年接待游客<span class="highlight">9738万人次</span>，实现旅游收入898亿元，文旅产业已成为全市经济的重要组成部分。</p>

<h2>二、经济发展格局</h2>
<h3>2.1 总体态势</h3>
<p>宜宾市经济呈现"一超多强"格局。翠屏区以1616.3亿元的GDP遥遥领先，占全市经济总量的40%以上，是全市经济的核心引擎。叙州区以676.07亿元位居第二，但与翠屏区差距明显。</p>
<div class="insight-box">
<strong>核心发现：</strong>翠屏区GDP是叙州区的2.4倍，是排名末位屏山县的12.5倍，区县间经济发展差距显著。
</div>

<h3>2.2 区县梯队划分</h3>
<table>
<tr><th>梯队</th><th>区县</th><th>2024年GDP</th><th>特征</th></tr>
<tr><td>第一梯队</td><td>翠屏区</td><td class="num">1616.3亿元</td><td>全市核心，白酒+新能源产业驱动</td></tr>
<tr><td>第二梯队</td><td>叙州区</td><td class="num">676.1亿元</td><td>城市副中心，高新技术产业</td></tr>
<tr><td>第三梯队</td><td>长宁县、高县、兴文县、珙县、筠连县</td><td class="num">210-231亿元</td><td>中游水平，文旅和农业资源较丰富</td></tr>
<tr><td>第四梯队</td><td>南溪区、江安县、屏山县</td><td class="num">约129-200亿元</td><td>体量较小，南溪和江安2024年负增长</td></tr>
</table>

<h3>2.3 增长动能分析</h3>
<p>2024年，受第五次全国经济普查影响，各区县GDP出现较大调整。兴文县（+7.9%）和屏山县（+7.8%）名义增速领先，表现最为出色。值得关注的是，<span class="highlight">江安县和南溪区出现负增长</span>，需关注其产业结构调整进度。</p>

<h2>三、财政状况分析</h2>
<h3>3.1 财政收入格局</h3>
<p>2024年各区县财政收入排名前三位为：翠屏区（38.0亿元）、叙州区（22.8亿元）、南溪区（16.8亿元）。市级财政收入115.94亿元，三江新区43.01亿元，均为全市财政重要来源。</p>
<div class="warning-box">
<strong>风险提示：</strong>高县税收收入同比下降7.58%，财政收入质量有所下滑；长宁县财政收入仅7.08亿元，财政实力最弱。
</div>

<h3>3.2 财政自给率</h3>
<p>财政自给率反映地区财政自给能力（财政收入/财政支出）。以2024年收入与2023年支出计算：</p>
<table>
<tr><th>区县</th><th>2024年收入(亿元)</th><th>2023年支出(亿元)</th><th>自给率</th><th>评价</th></tr>
{''.join(fiscal_rows)}
</table>

<h3>3.3 市级财政趋势</h3>
<p>2023年全市一般公共预算收入313.9亿元，2024年增长至324.3亿元，增速3.3%。税收占比维持在58.8%左右，财政收入质量相对稳定。2025年1-5月，全市地方一般公共预算收入175.99亿元，同比增长6.4%，开局良好。</p>

<h2>四、文旅发展分析</h2>
<h3>4.1 总体规模</h3>
<p>2024年宜宾市共接待游客9738万人次，实现旅游收入898亿元。按全市GDP4005.76亿元计算，<span class="highlight">旅游收入占GDP比重达22.4%</span>，文旅产业对经济的贡献度较高。</p>

<h3>4.2 核心资源分布</h3>
<p>宜宾市文旅资源呈现明显的区县集中特征：</p>
<ul>
<li><strong>翠屏区：</strong>五粮液景区（工业旅游）、李庄古镇（历史文化）、城市文旅综合体</li>
<li><strong>长宁县：</strong>蜀南竹海（4A级，自然风光龙头）、七洞沟</li>
<li><strong>兴文县：</strong>兴文石海（4A级，地质奇观）、僰王山</li>
</ul>
<div class="insight-box">
<strong>文旅-财政交叉分析：</strong>拥有核心文旅资源的长宁县和兴文县，财政收入分别仅7.08亿元和15.52亿元，处于全市末位。文旅资源优势尚未充分转化为财政实力，"文旅强、财政弱"现象明显。
</div>

<h3>4.3 发展瓶颈</h3>
<p>1. <strong>区县文旅数据缺失：</strong>目前公开渠道仅能获取市级层面的游客接待量和旅游收入，各区县细分数据极少披露，不利于精准施策。</p>
<p>2. <strong>资源转化效率待提升：</strong>核心景区多位于经济欠发达区县，基础设施和配套服务仍有提升空间。</p>
<p>3. <strong>品牌联动不足：</strong>蜀南竹海、兴文石海、李庄古镇等核心景区相对独立，缺乏统一的旅游线路串联和营销整合。</p>

<h2>五、核心结论与建议</h2>
<h3>5.1 核心结论</h3>
<p>1. <strong>经济集中度极高：</strong>翠屏区独占全市40%以上的GDP，区县发展不均衡问题突出。</p>
<p>2. <strong>财政自给率偏低：</strong>多数区县财政自给率不足50%，对上级转移支付依赖度较高。</p>
<p>3. <strong>文旅贡献显著但转化不足：</strong>旅游收入占GDP超22%，但文旅资源丰富的区县财政收入排名靠后。</p>
<p>4. <strong>部分区县增长乏力：</strong>南溪区和江安县2024年GDP负增长，需警惕经济下行风险。</p>

<h3>5.2 政策建议</h3>
<p><strong>对财政方面：</strong></p>
<ul>
<li>优化税收结构，提高税收占比，减少非税收入依赖</li>
<li>加强财源建设，培育可持续的税收增长点</li>
<li>建立区县财政风险预警机制，关注自给率持续下降的区县</li>
</ul>
<p><strong>对文旅方面：</strong></p>
<ul>
<li>建立区县文旅统计体系，定期披露游客量和旅游收入数据</li>
<li>推动"文旅+"融合发展，提升景区周边消费带动能力</li>
<li>构建统一的长江文旅品牌，串联核心景区形成精品旅游线路</li>
<li>支持兴文县、长宁县等文旅资源富集区发展文旅配套产业</li>
</ul>

<div class="footer">
<p>本报告基于公开政府统计数据整理分析</p>
<p>数据更新日期：2025年7月 | 分析工具：Python + ECharts</p>
</div>
</body>
</html>
'''
    return html


def generate_readme():
    return '''# 宜宾市各区县财政与文旅数据分析

> 基于 2021-2025 年公开政府统计数据，构建交互式数据看板与深度分析报告

## 项目结构

```
.
├── data/
│   └── yibin_data.json          # 原始数据集（JSON格式）
├── scripts/
│   └── generate_dashboard.py    # 数据看板与报告生成脚本
├── dashboard/
│   └── index.html               # 交互式数据看板（可部署到GitHub Pages）
├── report/
│   └── report.html              # 深度分析报告
└── README.md                    # 项目说明
```

## 数据看板

交互式看板包含以下模块：

- **全市GDP趋势图**：2020-2024年宜宾市GDP变化
- **区县GDP排名**：2024年各区县GDP横向对比
- **财政收入排名**：2024年各区县一般公共预算收入
- **GDP趋势对比**：10个区县五年变化折线图
- **财政自给率**：收入/支出比的可视化分析
- **人均GDP估算**：基于常住人口计算
- **全市财政趋势**：收入、税收、支出对比
- **交互式数据表格**：GDP/财政/文旅三维度切换

## 核心发现

| 维度 | 关键结论 |
|------|---------|
| 经济格局 | 翠屏区GDP占全市40%+，"一超多强"格局明显 |
| 财政自给 | 多数区县自给率<50%，依赖转移支付 |
| 文旅贡献 | 旅游收入占GDP 22.4%，但资源转化效率不足 |
| 增长分化 | 兴文、屏山增速领先，南溪、江安负增长 |

## 数据来源

- 宜宾市统计局国民经济和社会发展统计公报
- 宜宾市财政局财政收支情况报告
- 宜宾市文旅局假日市场统计
- 各区县政府门户网站公开数据

## 技术栈

- **数据处理**：Python 3 + JSON
- **可视化**：ECharts 5
- **前端**：纯HTML/CSS/JavaScript，零依赖（除ECharts CDN）
- **部署**：支持GitHub Pages静态托管

## 使用方式

1. 直接在浏览器中打开 `dashboard/index.html` 查看交互式看板
2. 打开 `report/report.html` 阅读分析报告
3. 修改 `data/yibin_data.json` 更新数据后，运行 `python scripts/generate_dashboard.py` 重新生成

## 数据说明

- 部分年份区县级数据因公开渠道限制存在缺失，已在JSON中标注为 `null`
- 人均GDP基于2022年常住人口数据计算
- 财政自给率 = 2024年财政收入 / 2023年财政支出
- 2025年数据仅包含1-5月累计值

## 许可证

本项目数据来源于政府公开渠道，仅供学习研究使用。
'''


def main():
    print("正在加载数据...")
    data = load_data()

    print("正在计算图表数据...")
    chart_data = compute_chart_data(data)
    rows_gdp, rows_fiscal = build_table_rows(data)

    print("正在生成交互式数据看板...")
    dashboard_html = generate_dashboard(data, chart_data, rows_gdp, rows_fiscal)
    with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    print(f"看板已生成: {DASHBOARD_PATH}")

    print("正在生成分析报告...")
    report_html = generate_report(data)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_html)
    print(f"报告已生成: {REPORT_PATH}")

    print("正在生成README...")
    readme = generate_readme()
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"README已生成: {README_PATH}")

    print("\n全部生成完成！")
    print(f"  看板: {DASHBOARD_PATH}")
    print(f"  报告: {REPORT_PATH}")
    print(f"  说明: {README_PATH}")


if __name__ == '__main__':
    main()
