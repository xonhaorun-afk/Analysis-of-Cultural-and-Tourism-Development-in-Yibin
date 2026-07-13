#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宜宾市各区县财政与文旅数据看板生成脚本
基于公开政府统计数据生成：交互式看板、地图看板、专题分析、深度分析报告
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'yibin_data.json')
GEOJSON_PATH = os.path.join(BASE_DIR, 'data', 'yibin_geojson.json')
DASHBOARD_PATH = os.path.join(BASE_DIR, 'dashboard', 'index.html')
MAP_PATH = os.path.join(BASE_DIR, 'dashboard', 'map.html')
THEMATIC_PATH = os.path.join(BASE_DIR, 'dashboard', 'thematic.html')
REPORT_PATH = os.path.join(BASE_DIR, 'report', 'report.html')
README_PATH = os.path.join(BASE_DIR, 'README.md')


def load_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_geojson():
    with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
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

    # 财政自给率 (2024收入 / 2024支出)
    self_ratio = {}
    for d in districts:
        rev = data['fiscal_revenue_2024'].get(d)
        exp = data['fiscal_expenditure'].get('2024', {}).get(d) or \
              data['fiscal_expenditure'].get('2023', {}).get(d)
        if rev is not None and exp is not None:
            self_ratio[d] = round(rev / exp * 100, 1)
    self_ratio_sorted = dict(sorted(self_ratio.items(), key=lambda x: x[1], reverse=True))

    # 人均GDP (2024)
    pc_gdp = {}
    for d in districts:
        g = data['gdp'].get('2024', {}).get(d)
        p = data['population_2024'].get(d)
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
        gdp22 = data['gdp'].get('2022', {}).get(d)
        gdp23 = data['gdp'].get('2023', {}).get(d)
        gdp24 = data['gdp'].get('2024', {}).get(d)
        pop = data['population_2024'].get(d)
        growth = data['gdp_growth_2024'].get(d)

        def fmt(v):
            return f"{v:.2f}" if isinstance(v, (int, float)) else "-"

        growth_html = "-"
        if isinstance(growth, (int, float)):
            cls = "up" if growth >= 0 else "down"
            growth_html = f'<span class="kpi-change {cls}">{growth:+.1f}%</span>'

        rows_gdp.append(
            f'<tr><td><strong>{d}</strong></td><td class="num">{fmt(gdp20)}</td>'
            f'<td class="num">{fmt(gdp21)}</td><td class="num">{fmt(gdp22)}</td>'
            f'<td class="num">{fmt(gdp23)}</td><td class="num"><strong>{fmt(gdp24)}</strong></td>'
            f'<td class="num">{growth_html}</td><td class="num">{fmt(pop)}</td></tr>'
        )

        rev = data['fiscal_revenue_2024'].get(d)
        exp = data['fiscal_expenditure'].get('2024', {}).get(d) or \
              data['fiscal_expenditure'].get('2023', {}).get(d)
        revs = fmt(rev)
        exps = fmt(exp)
        ratio_s = "-"
        if isinstance(rev, (int, float)) and isinstance(exp, (int, float)):
            ratio_s = f"{rev/exp*100:.1f}%"
        pc_s = "-"
        if isinstance(rev, (int, float)) and isinstance(pop, (int, float)):
            pc_s = f"{rev*10000/pop:.0f}"
        rev_growth = data['fiscal_revenue_growth_2024'].get(d)
        rev_growth_html = "-"
        if isinstance(rev_growth, (int, float)):
            cls = "up" if rev_growth >= 0 else "down"
            rev_growth_html = f'<span class="kpi-change {cls}">{rev_growth:+.1f}%</span>'

        rows_fiscal.append(
            f'<tr><td><strong>{d}</strong></td><td class="num">{revs}</td>'
            f'<td class="num">{exps}</td><td class="num">{ratio_s}</td>'
            f'<td class="num">{rev_growth_html}</td><td class="num">{pc_s}</td></tr>'
        )

    return "\n".join(rows_gdp), "\n".join(rows_fiscal)


def generate_dashboard(data, chart_data, rows_gdp, rows_fiscal):
    """生成原版交互式数据看板HTML"""
    districts = data['districts']
    scenic_cards = "\n".join(
        f'<div class="scenic-card"><div class="scenic-name">{s["name"]}</div>'
        f'<div class="scenic-meta"><span class="badge badge-primary">{s["level"]}</span>'
        f'<span class="badge badge-success">{s["district"]}</span>'
        f'<span class="badge badge-warning">{s["type"]}</span></div></div>'
        for s in data['scenic_spots']
    )

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
.nav-bar{{
  background:#fff;padding:12px 24px;box-shadow:0 2px 4px rgba(0,0,0,.05);
  display:flex;gap:24px;align-items:center;position:sticky;top:0;z-index:10
}}
.nav-bar a{{color:#1a5276;text-decoration:none;font-weight:500;font-size:.95em}}
.nav-bar a:hover{{color:#2980b9}}
.nav-bar a.active{{border-bottom:2px solid #1a5276;padding-bottom:4px}}
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
  display:inline-block;padding:2px 10px;border-radius:12px;font-size:.8em;font-weight:500;margin-right:4px
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
<div class="nav-bar">
  <a href="index.html" class="active">综合看板</a>
  <a href="map.html">地图看板</a>
  <a href="thematic.html">专题分析</a>
  <a href="../report/report.html" target="_blank">分析报告</a>
</div>
<div class="header">
  <h1>宜宾市各区县财政与文旅数据分析看板</h1>
  <p>基于 2020-2024 年公开政府统计数据 | 数据驱动决策</p>
</div>

<div class="container">
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-label">2024年全市GDP</div>
      <div class="kpi-value">4005.8<span style="font-size:.5em">亿元</span></div>
      <div class="kpi-change up">四川省第3位 · 同比+5.0%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">2024年财政收入</div>
      <div class="kpi-value">324.3<span style="font-size:.5em">亿元</span></div>
      <div class="kpi-change up">全省第2位 · 增长3.3%</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">2024年接待游客</div>
      <div class="kpi-value">9739.8<span style="font-size:.5em">万人次</span></div>
      <div class="kpi-change up">+9.42% · 收入 898.2亿元</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">人均GDP (2024)</div>
      <div class="kpi-value">8.69<span style="font-size:.5em">万元</span></div>
      <div class="kpi-change up">常住人口461.1万</div>
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
      <div class="section-title">财政自给率（2024收入/2023或2024支出）</div>
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
        <thead><tr><th>区县</th><th>2020年GDP</th><th>2021年GDP</th><th>2022年GDP</th><th>2023年GDP</th><th>2024年GDP</th><th>2024增速</th><th>人口(万)</th></tr></thead>
        <tbody>
{rows_gdp}
        </tbody>
      </table>
    </div>
    <div id="tab-fiscal" class="tab-content">
      <table class="data-table">
        <thead><tr><th>区县</th><th>2024年收入(亿元)</th><th>2023/2024年支出(亿元)</th><th>财政自给率</th><th>收入同比</th><th>人均财力(元/人)</th></tr></thead>
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
          <thead><tr><th>指标</th><th>数值</th><th>同比</th></tr></thead>
          <tbody>
            <tr><td>游客接待量</td><td class="num">9739.82万人次</td><td class="num">+9.42%</td></tr>
            <tr><td>旅游总收入</td><td class="num">898.22亿元</td><td class="num">+11.61%</td></tr>
            <tr><td>A级景区数量</td><td class="num">55家</td><td class="num">-</td></tr>
            <tr><td>4A级景区（已收录）</td><td class="num">7家</td><td class="num">-</td></tr>
            <tr><td>旅游收入占GDP比重</td><td class="num">22.4%</td><td class="num">-</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<div class="footer">
  <p>数据来源：宜宾市统计局、财政局、文旅局公开数据 | 更新时间：2026年7月</p>
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

const chartGdpTrend = echarts.init(document.getElementById('chart-gdp-trend'));
chartGdpTrend.setOption({{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: {json.dumps(districts, ensure_ascii=False)}, top: 0, textStyle: {{ fontSize: 11 }} }},
  xAxis: {{ type: 'category', data: CHART_DATA.city_gdp_years }},
  yAxis: {{ type: 'value', name: '亿元' }},
  series: CHART_DATA.gdp_series
}});

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


def generate_map_dashboard(data, geojson):
    """生成地图看板 HTML：ECharts 地图 + 时间轴 + 指标切换 + hover 详情"""
    districts = data['districts']
    centers = data['district_centers']

    # 构建地图时间序列数据：每年每个区县的各指标值
    years = ['2020', '2021', '2022', '2023', '2024']
    metrics = {
        'gdp': {'label': 'GDP (亿元)', 'unit': '亿元', 'source_key': 'gdp'},
        'revenue': {'label': '财政收入 (亿元)', 'unit': '亿元', 'source_key': 'fiscal_revenue_2024'},
        'self_ratio': {'label': '财政自给率 (%)', 'unit': '%', 'source_key': 'self_ratio'},
        'pc_gdp': {'label': '人均GDP (元/人)', 'unit': '元/人', 'source_key': 'pc_gdp'},
        'visitors': {'label': '接待游客 (万人次)', 'unit': '万人次', 'source_key': 'visitors'},
        'tourism_revenue': {'label': '旅游收入 (亿元)', 'unit': '亿元', 'source_key': 'tourism_revenue'},
    }

    # 构造每年每个指标的数据
    map_data_by_year_metric = {}
    for year in years:
        map_data_by_year_metric[year] = {}
        # GDP
        gdp_data = []
        for d in districts:
            v = data['gdp'].get(year, {}).get(d)
            gdp_data.append({'name': d, 'value': v})
        map_data_by_year_metric[year]['gdp'] = gdp_data

        # 财政收入 - 只用 2024 年
        rev_data = []
        for d in districts:
            v = data['fiscal_revenue_2024'].get(d) if year == '2024' else None
            rev_data.append({'name': d, 'value': v if year == '2024' else None})
        map_data_by_year_metric[year]['revenue'] = rev_data

        # 财政自给率
        sr_data = []
        for d in districts:
            rev = data['fiscal_revenue_2024'].get(d) if year == '2024' else None
            exp_24 = data['fiscal_expenditure'].get('2024', {}).get(d)
            exp_23 = data['fiscal_expenditure'].get('2023', {}).get(d)
            exp = exp_24 or exp_23 if year == '2024' else None
            v = round(rev/exp*100, 1) if (rev is not None and exp is not None) else None
            sr_data.append({'name': d, 'value': v if year == '2024' else None})
        map_data_by_year_metric[year]['self_ratio'] = sr_data

        # 人均GDP
        pc_data = []
        for d in districts:
            g = data['gdp'].get(year, {}).get(d)
            p = data['population_2024'].get(d)
            v = round(g*10000/p, 0) if (g is not None and p is not None) else None
            pc_data.append({'name': d, 'value': v})
        map_data_by_year_metric[year]['pc_gdp'] = pc_data

        # 接待游客 - 只有 2024
        vis_data = []
        for d in districts:
            v = data['tourism_district_2024'].get(d, {}).get('游客万人次') if year == '2024' else None
            vis_data.append({'name': d, 'value': v if year == '2024' else None})
        map_data_by_year_metric[year]['visitors'] = vis_data

        # 旅游收入
        tr_data = []
        for d in districts:
            v = data['tourism_district_2024'].get(d, {}).get('旅游收入亿元') if year == '2024' else None
            tr_data.append({'name': d, 'value': v if year == '2024' else None})
        map_data_by_year_metric[year]['tourism_revenue'] = tr_data

    # 全量数据
    all_data_by_metric = {
        'gdp': {d: [data['gdp'].get(y, {}).get(d) for y in years] for d in districts},
        'revenue': {d: [data['fiscal_revenue_2024'].get(d) if y == '2024' else None for y in years] for d in districts},
        'self_ratio': {d: [round((data['fiscal_revenue_2024'].get(d) / (data['fiscal_expenditure'].get('2024', {}).get(d) or data['fiscal_expenditure'].get('2023', {}).get(d)))*100, 1) if y == '2024' and data['fiscal_revenue_2024'].get(d) is not None and (data['fiscal_expenditure'].get('2024', {}).get(d) or data['fiscal_expenditure'].get('2023', {}).get(d)) is not None else None for y in years] for d in districts},
        'pc_gdp': {d: [round(data['gdp'].get(y, {}).get(d) * 10000 / data['population_2024'].get(d), 0) if data['gdp'].get(y, {}).get(d) is not None else None for y in years] for d in districts},
        'visitors': {d: [data['tourism_district_2024'].get(d, {}).get('游客万人次') if y == '2024' else None for y in years] for d in districts},
        'tourism_revenue': {d: [data['tourism_district_2024'].get(d, {}).get('旅游收入亿元') if y == '2024' else None for y in years] for d in districts},
    }

    map_data_json = json.dumps(map_data_by_year_metric, ensure_ascii=False)
    all_data_json = json.dumps(all_data_by_metric, ensure_ascii=False)
    geojson_json = json.dumps(geojson, ensure_ascii=False)
    centers_json = json.dumps(centers, ensure_ascii=False)

    # 区县完整资料（用于 tooltip）
    district_info = {}
    for d in districts:
        gdp20 = data['gdp'].get('2020', {}).get(d)
        gdp24 = data['gdp'].get('2024', {}).get(d)
        gr = data['gdp_growth_2024'].get(d)
        rev = data['fiscal_revenue_2024'].get(d)
        exp = data['fiscal_expenditure'].get('2024', {}).get(d) or data['fiscal_expenditure'].get('2023', {}).get(d)
        ratio = round(rev/exp*100, 1) if (rev is not None and exp is not None) else None
        pop = data['population_2024'].get(d)
        pc = round(gdp24*10000/pop, 0) if (gdp24 and pop) else None
        vis = data['tourism_district_2024'].get(d, {}).get('游客万人次')
        tr = data['tourism_district_2024'].get(d, {}).get('旅游收入亿元')
        brand = data['tourism_branding'].get(d, '-')
        district_info[d] = {
            'gdp_2020': gdp20, 'gdp_2024': gdp24, 'growth': gr,
            'revenue': rev, 'expenditure': exp, 'self_ratio': ratio,
            'population': pop, 'pc_gdp': pc,
            'visitors': vis, 'tourism_revenue': tr, 'branding': brand
        }
    district_info_json = json.dumps(district_info, ensure_ascii=False, indent=2)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>宜宾地图看板 - 财政与文旅时空分析</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans SC",sans-serif;
  background:#0e1a2b;color:#e0e6ed;line-height:1.6
}}
.nav-bar{{
  background:rgba(255,255,255,.05);padding:12px 24px;backdrop-filter:blur(10px);
  display:flex;gap:24px;align-items:center;border-bottom:1px solid rgba(255,255,255,.08)
}}
.nav-bar a{{color:#7e9ec9;text-decoration:none;font-weight:500;font-size:.95em;transition:color .2s}}
.nav-bar a:hover{{color:#fff}}
.nav-bar a.active{{color:#fff;border-bottom:2px solid #f39c12;padding-bottom:4px}}
.header{{
  padding:30px 20px;text-align:center;background:linear-gradient(180deg,#0e1a2b 0%,#16273f 100%)
}}
.header h1{{font-size:2em;color:#fff;margin-bottom:6px;letter-spacing:1px}}
.header p{{color:#7e9ec9;font-size:.95em}}
.container{{display:grid;grid-template-columns:1fr 380px;gap:20px;padding:20px;max-width:1600px;margin:0 auto}}
.panel{{
  background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
  border-radius:12px;padding:20px;backdrop-filter:blur(10px)
}}
.controls{{
  display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:16px
}}
.control-label{{color:#7e9ec9;font-size:.85em;margin-right:6px}}
.metric-btns{{display:flex;gap:6px;flex-wrap:wrap}}
.metric-btn{{
  padding:6px 14px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);
  color:#7e9ec9;border-radius:6px;cursor:pointer;font-size:.85em;transition:all .2s
}}
.metric-btn:hover{{background:rgba(255,255,255,.1);color:#fff}}
.metric-btn.active{{background:#f39c12;color:#1a2530;border-color:#f39c12;font-weight:600}}
#chart-map{{width:100%;height:600px;background:rgba(255,255,255,.02);border-radius:8px}}
.year-slider{{
  display:flex;align-items:center;gap:8px;padding:10px 0
}}
.year-slider input{{flex:1;accent-color:#f39c12}}
.year-display{{
  font-size:1.4em;font-weight:700;color:#f39c12;min-width:60px;text-align:right
}}
.ranking-panel h3{{
  color:#fff;font-size:1.05em;margin-bottom:12px;padding-bottom:8px;
  border-bottom:1px solid rgba(255,255,255,.1)
}}
.ranking-list{{list-style:none;padding:0;margin:0}}
.ranking-list li{{
  display:flex;justify-content:space-between;align-items:center;padding:8px 12px;
  margin-bottom:4px;background:rgba(255,255,255,.03);border-radius:6px;
  border-left:3px solid transparent;transition:all .2s;cursor:pointer
}}
.ranking-list li:hover{{background:rgba(255,255,255,.08);border-left-color:#f39c12}}
.ranking-list li.no1{{border-left-color:#f39c12;background:rgba(243,156,18,.1)}}
.ranking-list li.no2{{border-left-color:#95a5a6}}
.ranking-list li.no3{{border-left-color:#cd853f}}
.rank-no{{color:#7e9ec9;font-weight:600;min-width:24px}}
.rank-name{{flex:1;color:#fff;font-size:.95em}}
.rank-val{{color:#f39c12;font-weight:600;font-family:monospace}}
.detail-panel{{margin-top:16px;padding:14px;background:rgba(255,255,255,.03);border-radius:8px;min-height:180px}}
.detail-panel h3{{color:#fff;margin-bottom:10px;font-size:1.05em}}
.detail-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.85em}}
.detail-item{{padding:6px 0}}
.detail-label{{color:#7e9ec9;font-size:.8em}}
.detail-value{{color:#fff;font-weight:600;font-family:monospace}}
.detail-branding{{margin-top:10px;padding:8px;background:rgba(243,156,18,.08);border-radius:6px;font-size:.85em;color:#f39c12}}
.footer{{text-align:center;padding:30px 20px;color:#7e9ec9;font-size:.85em;border-top:1px solid rgba(255,255,255,.05)}}
@media(max-width:1100px){{
  .container{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
<div class="nav-bar">
  <a href="index.html">综合看板</a>
  <a href="map.html" class="active">地图看板</a>
  <a href="thematic.html">专题分析</a>
  <a href="../report/report.html" target="_blank">分析报告</a>
</div>
<div class="header">
  <h1>宜宾市各区县财政与文旅地图看板</h1>
  <p>实时地图 · 时间轴 · 指标切换 · 鼠标悬停查看详情</p>
</div>

<div class="container">
  <div>
    <div class="panel">
      <div class="controls">
        <span class="control-label">指标：</span>
        <div class="metric-btns">
          <button class="metric-btn active" data-metric="gdp">GDP</button>
          <button class="metric-btn" data-metric="revenue">财政收入</button>
          <button class="metric-btn" data-metric="self_ratio">财政自给率</button>
          <button class="metric-btn" data-metric="pc_gdp">人均GDP</button>
          <button class="metric-btn" data-metric="visitors">接待游客</button>
          <button class="metric-btn" data-metric="tourism_revenue">旅游收入</button>
        </div>
      </div>
      <div class="year-slider">
        <span class="control-label">年份：</span>
        <input type="range" id="year-slider" min="0" max="4" value="4" step="1">
        <span class="year-display" id="year-display">2024</span>
      </div>
      <div id="chart-map"></div>
    </div>
  </div>

  <div>
    <div class="panel ranking-panel">
      <h3 id="ranking-title">2024年 GDP 排名</h3>
      <ul class="ranking-list" id="ranking-list"></ul>
    </div>
    <div class="panel detail-panel">
      <h3>区县详情 <span id="detail-name" style="color:#f39c12"></span></h3>
      <div class="detail-grid" id="detail-grid"></div>
      <div class="detail-branding" id="detail-branding" style="display:none"></div>
    </div>
  </div>
</div>

<div class="footer">
  <p>数据来源：宜宾市统计局、财政局、文旅局公开数据</p>
  <p>地图数据：阿里 DataV.GeoAtlas (adcode: 511500)</p>
</div>

<script>
const MAP_DATA = {map_data_json};
const ALL_DATA = {all_data_json};
const GEOJSON = {geojson_json};
const CENTERS = {centers_json};
const DISTRICT_INFO = {district_info_json};

const YEARS = ['2020','2021','2022','2023','2024'];
const METRICS = {{
  gdp: {{name:'GDP', unit:'亿元', key:'亿元'}},
  revenue: {{name:'财政收入', unit:'亿元', key:'亿元'}},
  self_ratio: {{name:'财政自给率', unit:'%', key:'%'}},
  pc_gdp: {{name:'人均GDP', unit:'元/人', key:'元'}},
  visitors: {{name:'接待游客', unit:'万人次', key:'万人次'}},
  tourism_revenue: {{name:'旅游收入', unit:'亿元', key:'亿元'}}
}};

let currentYear = '2024';
let currentMetric = 'gdp';
let mapChart = null;

echarts.registerMap('yibin', GEOJSON);

function fmt(v, metric) {{
  if (v === null || v === undefined) return '-';
  if (metric === 'pc_gdp') return (v/10000).toFixed(1) + '万';
  if (metric === 'self_ratio') return v.toFixed(1) + '%';
  return v.toFixed(1);
}}

function renderMap() {{
  const data = MAP_DATA[currentYear][currentMetric];
  const metric = METRICS[currentMetric];
  const values = data.map(d => d.value).filter(v => v !== null);
  const minV = Math.min(...values);
  const maxV = Math.max(...values);

  const option = {{
    tooltip: {{
      trigger: 'item',
      backgroundColor: 'rgba(14,26,43,.95)',
      borderColor: '#f39c12',
      borderWidth: 1,
      textStyle: {{ color: '#fff', fontSize: 13 }},
      formatter: function(p) {{
        if (!p.data) return p.name;
        const d = p.data;
        const info = DISTRICT_INFO[p.name];
        if (!info) return `<b>${{p.name}}</b><br/>${{metric.name}}: ${{fmt(d.value, currentMetric)}}`;
        return `
          <b style="color:#f39c12;font-size:15px">${{p.name}}</b><br/>
          <span style="color:#7e9ec9">${{currentYear}}年 ${{metric.name}}</span><br/>
          <b style="font-size:16px;color:#fff">${{fmt(d.value, currentMetric)}} ${{metric.key}}</b><br/>
          <hr style="border-color:rgba(255,255,255,.1);margin:6px 0"/>
          GDP: ${{info.gdp_2024||'-'}} 亿元 (${{info.growth>=0?'+':''}}${{info.growth||0}}%)<br/>
          财政收入: ${{info.revenue||'-'}} 亿元<br/>
          财政自给率: ${{info.self_ratio||'-'}}%<br/>
          人口: ${{info.population||'-'}} 万人<br/>
          人均GDP: ${{info.pc_gdp ? (info.pc_gdp/10000).toFixed(1) + '万' : '-'}}<br/>
          接待游客: ${{info.visitors||'-'}} 万人次
        `;
      }}
    }},
    visualMap: {{
      min: minV,
      max: maxV,
      left: 20, bottom: 20,
      text: ['高','低'],
      calculable: true,
      textStyle: {{ color: '#7e9ec9' }},
      inRange: {{
        color: ['#1a3a5c', '#2980b9', '#f39c12', '#e74c3c']
      }}
    }},
    geo: {{
      map: 'yibin',
      roam: true,
      zoom: 1.15,
      label: {{
        show: true,
        color: '#fff',
        fontSize: 11
      }},
      itemStyle: {{
        borderColor: 'rgba(243,156,18,.6)',
        borderWidth: 1,
        shadowColor: 'rgba(0,0,0,.5)',
        shadowBlur: 10
      }},
      emphasis: {{
        label: {{ show: true, color: '#fff', fontSize: 14, fontWeight: 'bold' }},
        itemStyle: {{
          areaColor: '#f39c12',
          borderColor: '#fff',
          borderWidth: 2
        }}
      }}
    }},
    series: [{{
      name: metric.name,
      type: 'map',
      geoIndex: 0,
      data: data
    }}]
  }};
  if (mapChart) {{
    mapChart.setOption(option, true);
  }} else {{
    mapChart = echarts.init(document.getElementById('chart-map'));
    mapChart.setOption(option);
    mapChart.on('click', function(p) {{
      showDistrictDetail(p.name);
    }});
  }}
}}

function updateRanking() {{
  const data = MAP_DATA[currentYear][currentMetric].filter(d => d.value !== null);
  data.sort((a,b) => b.value - a.value);
  const metric = METRICS[currentMetric];
  document.getElementById('ranking-title').textContent = `${{currentYear}}年 ${{metric.name}} 排名`;
  const list = document.getElementById('ranking-list');
  list.innerHTML = data.map((d, i) =>
    `<li class="${{i<3?'no'+(i+1):''}}" onclick="showDistrictDetail('${{d.name}}')">
      <span class="rank-no">${{i+1}}</span>
      <span class="rank-name">${{d.name}}</span>
      <span class="rank-val">${{fmt(d.value, currentMetric)}}</span>
    </li>`
  ).join('');
}}

function showDistrictDetail(name) {{
  const info = DISTRICT_INFO[name];
  if (!info) return;
  document.getElementById('detail-name').textContent = '· ' + name;
  document.getElementById('detail-grid').innerHTML = `
    <div class="detail-item"><div class="detail-label">2020 GDP</div><div class="detail-value">${{info.gdp_2020||'-'}} 亿元</div></div>
    <div class="detail-item"><div class="detail-label">2024 GDP</div><div class="detail-value">${{info.gdp_2024||'-'}} 亿元</div></div>
    <div class="detail-item"><div class="detail-label">2024 增速</div><div class="detail-value" style="color:${{info.growth>=0?'#27ae60':'#e74c3c'}}">${{info.growth>=0?'+':''}}${{info.growth||0}}%</div></div>
    <div class="detail-item"><div class="detail-label">常住人口</div><div class="detail-value">${{info.population||'-'}} 万</div></div>
    <div class="detail-item"><div class="detail-label">人均GDP</div><div class="detail-value">${{info.pc_gdp ? (info.pc_gdp/10000).toFixed(1) + ' 万' : '-'}}</div></div>
    <div class="detail-item"><div class="detail-label">财政收入</div><div class="detail-value">${{info.revenue||'-'}} 亿元</div></div>
    <div class="detail-item"><div class="detail-label">财政自给率</div><div class="detail-value">${{info.self_ratio||'-'}}%</div></div>
    <div class="detail-item"><div class="detail-label">接待游客</div><div class="detail-value">${{info.visitors||'-'}} 万人次</div></div>
  `;
  const brand = info.branding;
  const brandingEl = document.getElementById('detail-branding');
  if (brand) {{
    brandingEl.style.display = 'block';
    brandingEl.innerHTML = '<b>文旅特色：</b>' + brand;
  }} else {{
    brandingEl.style.display = 'none';
  }}
}}

// 事件绑定
document.querySelectorAll('.metric-btn').forEach(btn => {{
  btn.addEventListener('click', function() {{
    document.querySelectorAll('.metric-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
    currentMetric = this.dataset.metric;
    renderMap();
    updateRanking();
  }});
}});

document.getElementById('year-slider').addEventListener('input', function() {{
  currentYear = YEARS[this.value];
  document.getElementById('year-display').textContent = currentYear;
  renderMap();
  updateRanking();
}});

window.addEventListener('resize', function() {{
  if (mapChart) mapChart.resize();
}});

renderMap();
updateRanking();
showDistrictDetail('翠屏区');
</script>
</body>
</html>
'''
    return html


def generate_thematic_dashboard(data):
    """生成专题分析页 HTML"""
    districts = data['districts']

    # 准备文旅-财政转化数据
    scatter_data = []
    for d in districts:
        rev = data['fiscal_revenue_2024'].get(d)
        gdp = data['gdp'].get('2024', {}).get(d)
        vis = data['tourism_district_2024'].get(d, {}).get('游客万人次')
        tr = data['tourism_district_2024'].get(d, {}).get('旅游收入亿元')
        brand = data['tourism_branding'].get(d, '')
        has_scenic = any(s['district'] == d for s in data['scenic_spots'])
        if gdp is not None and rev is not None:
            scatter_data.append({
                'name': d,
                'gdp': gdp, 'revenue': rev,
                'visitors': vis, 'tourism_revenue': tr,
                'has_scenic': has_scenic, 'brand': brand
            })

    # 增长动能分组
    growth_data = []
    for d in districts:
        g = data['gdp_growth_2024'].get(d)
        if g is not None:
            growth_data.append({'name': d, 'growth': g})
    growth_data.sort(key=lambda x: x['growth'], reverse=True)

    # 区县梯队 (按 2024 GDP)
    gdp_2024 = [(d, data['gdp'].get('2024', {}).get(d)) for d in districts]
    gdp_2024 = [(d, v) for d, v in gdp_2024 if v is not None]
    gdp_2024.sort(key=lambda x: x[1], reverse=True)

    # 文旅资源密度 (4A景区数 / 人口)
    scenic_per_district = {}
    for s in data['scenic_spots']:
        d = s['district']
        scenic_per_district[d] = scenic_per_district.get(d, 0) + 1

    # 产业占比数据
    industry_data = data['industry_structure_2024']

    scatter_json = json.dumps(scatter_data, ensure_ascii=False)
    growth_json = json.dumps(growth_data, ensure_ascii=False)
    gdp_2024_json = json.dumps(gdp_2024, ensure_ascii=False)
    scenic_per_json = json.dumps(scenic_per_district, ensure_ascii=False)
    industry_json = json.dumps(industry_data, ensure_ascii=False)
    districts_json = json.dumps(districts, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>宜宾专题分析 - 文旅-财政交叉视角</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans SC",sans-serif;
  background:#f5f7fa;color:#333;line-height:1.6
}}
.nav-bar{{
  background:#fff;padding:12px 24px;box-shadow:0 2px 4px rgba(0,0,0,.05);
  display:flex;gap:24px;align-items:center;position:sticky;top:0;z-index:10
}}
.nav-bar a{{color:#1a5276;text-decoration:none;font-weight:500;font-size:.95em}}
.nav-bar a:hover{{color:#2980b9}}
.nav-bar a.active{{border-bottom:2px solid #1a5276;padding-bottom:4px}}
.header{{
  background:linear-gradient(135deg,#7d3c98 0%,#af7ac5 100%);
  color:white;padding:40px 20px;text-align:center
}}
.header h1{{font-size:2.1em;margin-bottom:8px}}
.header p{{opacity:.92;font-size:1.05em}}
.container{{max-width:1400px;margin:0 auto;padding:20px}}
.section{{
  background:white;border-radius:12px;padding:28px;margin:20px 0;box-shadow:0 2px 8px rgba(0,0,0,.06)
}}
.section-title{{
  font-size:1.35em;font-weight:600;color:#7d3c98;margin-bottom:8px;
  padding-bottom:12px;border-bottom:2px solid #f0e6f5
}}
.section-subtitle{{color:#888;font-size:.92em;margin-bottom:18px}}
.chart-container{{width:100%;height:480px;margin:16px 0}}
.chart-grid{{
  display:grid;grid-template-columns:repeat(auto-fit,minmax(520px,1fr));gap:20px
}}
.chart-grid .section{{margin:0}}
.insight-box{{
  background:linear-gradient(135deg,#f4ecf7 0%,#faf5fc 100%);
  border-left:4px solid #7d3c98;padding:18px;margin:18px 0;border-radius:0 8px 8px 0
}}
.insight-box strong{{color:#7d3c98}}
.footer{{text-align:center;padding:40px 20px;color:#999;font-size:.9em}}
</style>
</head>
<body>
<div class="nav-bar">
  <a href="index.html">综合看板</a>
  <a href="map.html">地图看板</a>
  <a href="thematic.html" class="active">专题分析</a>
  <a href="../report/report.html" target="_blank">分析报告</a>
</div>
<div class="header">
  <h1>宜宾文旅-财政交叉专题分析</h1>
  <p>穿透表象看结构 · 数据交叉验证结论</p>
</div>

<div class="container">

  <div class="section">
    <div class="section-title">专题一：文旅资源 vs 财政实力</div>
    <div class="section-subtitle">散点图：X=GDP(亿元), Y=财政收入(亿元)，点大小=接待游客量，颜色区分是否有4A景区</div>
    <div id="chart-scatter" class="chart-container"></div>
    <div class="insight-box">
      <strong>核心洞察：</strong>拥有蜀南竹海、兴文石海等核心4A景区的长宁、兴文两县，GDP虽处于全市中游，但财政收入排名靠后（长宁7.08亿、兴文15.52亿）。翠屏区凭借五粮液+李庄古镇实现"文旅与财政双高"，但叙州区作为城市副中心，文旅资源相对薄弱，财政仍居全市第二。说明<strong>文旅资源≠财政实力</strong>，工业基础和白酒产业才是宜宾财政的核心引擎。
    </div>
  </div>

  <div class="chart-grid">
    <div class="section">
      <div class="section-title">专题二：2024 增长动能分组</div>
      <div class="section-subtitle">按GDP增速从高到低排序</div>
      <div id="chart-growth" class="chart-container"></div>
    </div>
    <div class="section">
      <div class="section-title">专题三：三次产业结构对比</div>
      <div class="section-subtitle">各区县一/二/三产占比</div>
      <div id="chart-industry" class="chart-container"></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">专题四：区县梯队综合画像</div>
    <div class="section-subtitle">按2024 GDP划分四个梯队，雷达图对比多维指标</div>
    <div id="chart-radar" class="chart-container"></div>
    <div class="insight-box">
      <strong>梯队结论：</strong>
      <ul style="margin:8px 0 0 20px;color:#555">
        <li><strong>第一梯队（&gt;1500亿）：</strong>翠屏区"一城独大"，占全市40.3%GDP，财政自给率超50%；</li>
        <li><strong>第二梯队（500-1000亿）：</strong>叙州区"城市副中心"，人均GDP偏低（7.06万）；</li>
        <li><strong>第三梯队（200-300亿）：</strong>7区"集群竞逐"，长宁/兴文走文旅路线，江安/南溪面临转型压力；</li>
        <li><strong>第四梯队（&lt;200亿）：</strong>屏山"追赶提速"（+4.6%），但产业基础最薄弱。</li>
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title">专题五：4A景区分布与区县财政匹配度</div>
    <div class="section-subtitle">横轴：4A景区数量，纵轴：财政收入（亿元）</div>
    <div id="chart-scenic" class="chart-container"></div>
    <div class="insight-box">
      <strong>关键发现：</strong>
      <ul style="margin:8px 0 0 20px;color:#555">
        <li>长宁拥有<strong>2个4A景区+1个国家级度假区</strong>，但财政收入仅7.08亿（全市最低），是"文旅强、财政弱"的典型；</li>
        <li>翠屏区4A景区数（2个）虽不及兴文县（2个），但因白酒产业支撑，财政收入38亿，差距悬殊；</li>
        <li>兴文、长宁等资源富集区需强化<strong>"门票→消费→税收"</strong>的转化链路，借鉴翠屏"工业反哺文旅"模式。</li>
      </ul>
    </div>
  </div>

  <div class="section">
    <div class="section-title">专题六：财政自给率 vs 文旅资源</div>
    <div class="section-subtitle">散点图：X=财政自给率(%)，Y=接待游客量(万人次)，象限分析</div>
    <div id="chart-quadrant" class="chart-container"></div>
  </div>

</div>

<div class="footer">
  <p>专题分析 · 基于公开政府统计数据整理</p>
  <p>数据更新日期：2026年7月 | 工具：Python + ECharts</p>
</div>

<script>
const SCATTER_DATA = {scatter_json};
const GROWTH_DATA = {growth_json};
const GDP_2024 = {gdp_2024_json};
const SCENIC_PER = {scenic_per_json};
const INDUSTRY = {industry_json};
const DISTRICTS = {districts_json};

const chartScatter = echarts.init(document.getElementById('chart-scatter'));
chartScatter.setOption({{
  tooltip: {{
    trigger: 'item',
    formatter: function(p) {{
      const d = p.data;
      return `<b>${{d[0]}}</b><br/>GDP: ${{d[1]}} 亿元<br/>财政收入: ${{d[2]}} 亿元<br/>接待游客: ${{d[3]||'-'}} 万人次<br/>${{d[4]?'含4A景区':'暂无4A'}}`;
    }}
  }},
  legend: {{ data: ['含4A景区','暂无4A'], top: 0, textStyle: {{ fontSize: 12 }} }},
  grid: {{ left: 70, right: 30, top: 40, bottom: 50 }},
  xAxis: {{
    name: 'GDP (亿元)', nameLocation: 'middle', nameGap: 30,
    type: 'value', axisLabel: {{ fontSize: 11 }}
  }},
  yAxis: {{
    name: '财政收入 (亿元)', nameLocation: 'middle', nameGap: 50,
    type: 'value', axisLabel: {{ fontSize: 11 }}
  }},
  series: [
    {{
      name: '含4A景区',
      type: 'scatter',
      symbolSize: function(d) {{ return Math.max(15, (d[3]||0)/20); }},
      data: SCATTER_DATA.filter(d => d.has_scenic).map(d => [d.name, d.gdp, d.revenue, d.visitors, d.has_scenic]),
      itemStyle: {{ color: '#e74c3c', opacity: 0.7 }},
      label: {{
        show: true, formatter: '{{@[0]}}', position: 'top', fontSize: 11, color: '#333'
      }}
    }},
    {{
      name: '暂无4A',
      type: 'scatter',
      symbolSize: 15,
      data: SCATTER_DATA.filter(d => !d.has_scenic).map(d => [d.name, d.gdp, d.revenue, d.visitors, d.has_scenic]),
      itemStyle: {{ color: '#3498db', opacity: 0.6 }},
      label: {{
        show: true, formatter: '{{@[0]}}', position: 'top', fontSize: 11, color: '#333'
      }}
    }}
  ]
}});

const chartGrowth = echarts.init(document.getElementById('chart-growth'));
chartGrowth.setOption({{
  tooltip: {{ trigger: 'axis', formatter: '{{b}}: {{c}}%' }},
  grid: {{ left: 50, right: 30, top: 20, bottom: 60 }},
  xAxis: {{
    type: 'category', data: GROWTH_DATA.map(d => d.name),
    axisLabel: {{ fontSize: 11, rotate: 25 }}
  }},
  yAxis: {{ type: 'value', name: '增速(%)', axisLabel: {{ formatter: '{{value}}%' }} }},
  series: [{{
    type: 'bar',
    data: GROWTH_DATA.map(d => ({{
      value: d.growth,
      itemStyle: {{ color: d.growth >= 5 ? '#27ae60' : d.growth >= 3 ? '#f39c12' : d.growth >= 0 ? '#3498db' : '#e74c3c' }}
    }})),
    label: {{ show: true, position: 'top', formatter: '{{c}}%', fontSize: 11 }},
    barWidth: '60%'
  }}]
}});

const chartIndustry = echarts.init(document.getElementById('chart-industry'));
const industryNames = Object.keys(INDUSTRY);
const industryData = industryNames.map(name => ({{
  name: name,
  value: [INDUSTRY[name]['一产'], INDUSTRY[name]['二产'], INDUSTRY[name]['三产']]
}}));
chartIndustry.setOption({{
  tooltip: {{ trigger: 'axis' }},
  legend: {{ data: ['一产', '二产', '三产'], top: 0 }},
  grid: {{ left: 50, right: 30, top: 40, bottom: 60 }},
  xAxis: {{
    type: 'category', data: industryNames,
    axisLabel: {{ fontSize: 11, rotate: 20 }}
  }},
  yAxis: {{ type: 'value', name: '占比(%)' }},
  series: [
    {{ name: '一产', type: 'bar', stack: '产业结构', data: industryData.map(d => d.value[0]), itemStyle: {{ color: '#27ae60' }} }},
    {{ name: '二产', type: 'bar', stack: '产业结构', data: industryData.map(d => d.value[1]), itemStyle: {{ color: '#2980b9' }} }},
    {{ name: '三产', type: 'bar', stack: '产业结构', data: industryData.map(d => d.value[2]), itemStyle: {{ color: '#f39c12' }} }}
  ]
}});

const chartRadar = echarts.init(document.getElementById('chart-radar'));
const tiers = [
  {{ name: '第一梯队：翠屏区', values: [1616, 38, 3860, 92.8, 6.5] }},
  {{ name: '第二梯队：叙州区', values: [676, 22.8, null, 95.8, 5.0] }},
  {{ name: '第三梯队：长宁县', values: [230.6, 7.08, 1517.6, 32.7, 4.5] }},
  {{ name: '第三梯队：兴文县', values: [225, 15.5, null, 37.8, 3.5] }},
  {{ name: '第四梯队：屏山县', values: [128.8, 11.6, 316, 24.2, 4.6] }}
];
chartRadar.setOption({{
  tooltip: {{}},
  legend: {{ data: tiers.map(t => t.name), top: 0, textStyle: {{ fontSize: 11 }} }},
  radar: {{
    indicator: [
      {{ name: 'GDP(亿元)', max: 1700 }},
      {{ name: '财政收入(亿元)', max: 40 }},
      {{ name: '游客(万人次)', max: 4000 }},
      {{ name: '人口(万)', max: 100 }},
      {{ name: '增速(%)', max: 8 }}
    ]
  }},
  series: [{{
    type: 'radar',
    data: tiers.map(t => ({{
      name: t.name,
      value: t.values.map((v, i) => i === 1 ? v : v)
    }}))
  }}]
}});

const chartScenic = echarts.init(document.getElementById('chart-scenic'));
const scenicData = DISTRICTS.map(d => ({{
  name: d,
  scenic: SCENIC_PER[d] || 0,
  revenue: 0
}})).map(d => ({{
  ...d,
  revenue: SCATTER_DATA.find(s => s.name === d.name)?.revenue || 0
}}));
chartScenic.setOption({{
  tooltip: {{ trigger: 'item' }},
  grid: {{ left: 50, right: 30, top: 20, bottom: 60 }},
  xAxis: {{
    type: 'category', data: scenicData.map(d => d.name),
    axisLabel: {{ fontSize: 11, rotate: 25 }}
  }},
  yAxis: [
    {{ type: 'value', name: '4A景区数', max: 4, position: 'left' }},
    {{ type: 'value', name: '财政收入(亿元)', position: 'right' }}
  ],
  series: [
    {{
      name: '4A景区数', type: 'bar', data: scenicData.map(d => d.scenic),
      itemStyle: {{ color: '#e74c3c' }}, barWidth: '40%',
      label: {{ show: true, position: 'top' }}
    }},
    {{
      name: '财政收入', type: 'line', yAxisIndex: 1,
      data: scenicData.map(d => d.revenue),
      itemStyle: {{ color: '#2980b9' }}, symbolSize: 10,
      lineStyle: {{ width: 3 }}
    }}
  ]
}});

const chartQuadrant = echarts.init(document.getElementById('chart-quadrant'));
const quadrantData = SCATTER_DATA
  .filter(d => d.visitors !== null)
  .map(d => ({{
    name: d.name,
    value: [d.self_ratio || 0, d.visitors, d.revenue]
  }}));
chartQuadrant.setOption({{
  tooltip: {{
    trigger: 'item',
    formatter: function(p) {{
      return `<b>${{p.data.name}}</b><br/>财政自给率: ${{p.value[0]}}%<br/>接待游客: ${{p.value[1]}} 万人次<br/>财政收入: ${{p.value[2]}} 亿元`;
    }}
  }},
  grid: {{ left: 60, right: 30, top: 30, bottom: 50 }},
  xAxis: {{ name: '财政自给率 (%)', nameLocation: 'middle', nameGap: 30, type: 'value' }},
  yAxis: {{ name: '接待游客 (万人次)', nameLocation: 'middle', nameGap: 45, type: 'value' }},
  series: [{{
    type: 'scatter',
    symbolSize: 20,
    data: quadrantData,
    itemStyle: {{ color: '#9b59b6', opacity: 0.7 }},
    label: {{ show: true, formatter: '{{@[0]}}', position: 'right', fontSize: 11 }}
  }}]
}});

window.addEventListener('resize', function() {{
  chartScatter.resize(); chartGrowth.resize(); chartIndustry.resize();
  chartRadar.resize(); chartScenic.resize(); chartQuadrant.resize();
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
        exp = data['fiscal_expenditure'].get('2024', {}).get(d) or data['fiscal_expenditure'].get('2023', {}).get(d)
        if rev is not None and exp is not None:
            ratio = rev / exp * 100
            if ratio >= 50:
                ev = "自给能力较强"
            elif ratio >= 30:
                ev = "自给能力一般，依赖转移支付"
            else:
                ev = "自给能力弱，高度依赖转移支付"
            growth = data['fiscal_revenue_growth_2024'].get(d, '')
            growth_str = f"{growth:+.1f}%" if isinstance(growth, (int, float)) else "-"
            fiscal_rows.append(
                f'<tr><td>{d}</td><td class="num">{rev:.2f}</td>'
                f'<td class="num">{exp:.2f}</td><td class="num">{ratio:.1f}%</td>'
                f'<td class="num">{growth_str}</td><td>{ev}</td></tr>'
            )

    # GDP 多年数据表
    gdp_rows = []
    for d in districts:
        g20 = data['gdp'].get('2020', {}).get(d)
        g24 = data['gdp'].get('2024', {}).get(d)
        g21 = data['gdp'].get('2021', {}).get(d)
        g22 = data['gdp'].get('2022', {}).get(d)
        g23 = data['gdp'].get('2023', {}).get(d)
        growth = data['gdp_growth_2024'].get(d)
        pop = data['population_2024'].get(d)

        def fmt(v):
            return f"{v:.2f}" if isinstance(v, (int, float)) else "-"

        pc = f"{(g24*10000/pop/10000):.1f}万" if (g24 and pop) else "-"
        gdp_rows.append(
            f'<tr><td><strong>{d}</strong></td>'
            f'<td class="num">{fmt(g20)}</td>'
            f'<td class="num">{fmt(g21)}</td>'
            f'<td class="num">{fmt(g22)}</td>'
            f'<td class="num">{fmt(g23)}</td>'
            f'<td class="num"><strong>{fmt(g24)}</strong></td>'
            f'<td class="num">{growth:+.1f}%</td>'
            f'<td class="num">{fmt(pop)}</td>'
            f'<td class="num">{pc}</td></tr>'
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
.nav-bar{{
  position:sticky;top:0;background:#fff;padding:10px 20px;
  box-shadow:0 2px 4px rgba(0,0,0,.05);text-align:center;
  border-bottom:1px solid #eee;margin:-40px -20px 24px
}}
.nav-bar a{{color:#1a5276;text-decoration:none;margin:0 12px;font-size:.92em}}
</style>
</head>
<body>
<div class="nav-bar">
  <a href="../dashboard/index.html">综合看板</a>
  <a href="../dashboard/map.html">地图看板</a>
  <a href="../dashboard/thematic.html">专题分析</a>
</div>
<h1>宜宾市各区县财政与文旅发展分析报告</h1>
<div class="meta">数据周期：2020-2024年 | 报告日期：2026年7月 | 数据来源：公开政府统计</div>

<h2>一、概述</h2>
<p>宜宾市位于四川省南部，地处川、滇、黔三省结合部，是长江上游区域中心城市。全市辖3区7县，总面积约1.33万平方公里，2024年末常住人口约<span class="highlight">461.1万人</span>。</p>
<p>2024年，宜宾市实现地区生产总值<span class="highlight">4005.76亿元</span>，经济总量排名四川省第三位；一般公共预算收入<span class="highlight">324.30亿元</span>，排名全省第二位。同年接待游客<span class="highlight">9739.82万人次</span>（同比+9.42%），实现旅游收入898.22亿元（同比+11.61%），文旅产业已成为全市经济的重要组成部分。</p>

<h2>二、经济发展格局</h2>
<h3>2.1 总体态势</h3>
<p>宜宾市经济呈现"<strong>一超多强</strong>"格局。翠屏区以1616.30亿元的GDP遥遥领先，占全市经济总量的<span class="highlight">40.3%</span>，是全市经济的核心引擎。叙州区以676.07亿元位居第二，但与翠屏区差距明显。</p>
<div class="insight-box">
<strong>核心发现：</strong>翠屏区GDP是叙州区的2.4倍，是排名末位屏山县的12.5倍，区县间经济发展差距显著。2024年翠屏区人均GDP达17.42万元，<span class="highlight">唯一超过全国平均线</span>（9.57万元）的区县；其余9个区县均低于全国平均。
</div>

<h3>2.2 区县梯队划分（基于2024 GDP）</h3>
<table>
<tr><th>梯队</th><th>区县</th><th>2024年GDP</th><th>特征</th></tr>
<tr><td>第一梯队</td><td>翠屏区</td><td class="num">1616.3亿元</td><td>全市核心，白酒+动力电池双引擎，二产占64.6%</td></tr>
<tr><td>第二梯队</td><td>叙州区</td><td class="num">676.1亿元</td><td>城市副中心，光伏储能产业，人口规模最大</td></tr>
<tr><td>第三梯队</td><td>长宁县、高县、江安县、南溪区、兴文县、珙县、筠连县</td><td class="num">210-232亿元</td><td>中游水平集群竞逐，差距不足21亿</td></tr>
<tr><td>第四梯队</td><td>屏山县</td><td class="num">128.8亿元</td><td>体量最小，脱贫后稳步增长</td></tr>
</table>

<h3>2.3 各区县GDP时间序列（亿元）</h3>
<table>
<tr><th>区县</th><th>2020</th><th>2021</th><th>2022</th><th>2023</th><th>2024</th><th>2024增速</th><th>人口(万)</th><th>人均GDP</th></tr>
{''.join(gdp_rows)}
</table>

<h3>2.4 增长动能分析</h3>
<p>2024年，受第五次全国经济普查影响，各区县GDP出现较大调整。兴文县（+3.5%实际增速，名义+7.9%）和屏山县（+4.6%实际增速，名义+7.8%）名义增速领先，表现最为出色。值得关注的是，<span class="highlight">江安县（+1.4%）和南溪区（+1.8%）增速疲软</span>，产业结构调整压力较大。</p>
<div class="warning-box">
<strong>增长分化：</strong>全市呈现"<strong>头部高增、中部分化、尾部追赶</strong>"格局：高县（+5.2%）、翠屏区（+6.5%）领跑，江安/南溪掉队，需警惕区域经济下行风险。
</div>

<h2>三、财政状况分析</h2>
<h3>3.1 财政收入格局</h3>
<p>2024年宜宾市地方一般公共预算收入324.30亿元，其中：<strong>市级115.94亿（35.8%）、三江新区43.01亿（13.3%）、各区县合计165.35亿（50.9%）</strong>。区县中前三：翠屏区38.00亿、叙州区22.83亿、南溪区16.79亿。</p>
<div class="warning-box">
<strong>风险提示：</strong>高县税收收入同比下降7.58%，财政收入质量有所下滑；长宁县财政收入仅7.08亿元，财政实力全市最弱。珙县2024年财政收入13.59亿元，同比大幅下降26.76%，主要因市场行情波动和政策调整，欧冶链金、中环国际等重点税源企业经营受冲击。
</div>

<h3>3.2 财政自给率</h3>
<p>财政自给率反映地区财政自给能力（财政收入/财政支出）。以2024年收入与2023/2024年支出计算：</p>
<table>
<tr><th>区县</th><th>2024年收入(亿元)</th><th>2023/2024年支出(亿元)</th><th>自给率</th><th>收入同比</th><th>评价</th></tr>
{''.join(fiscal_rows)}
</table>
<p>全市9个可比区县中，<strong>仅翠屏区自给率超过50%</strong>，其余均在30%-47%之间，对上级转移支付依赖度较高。值得关注的是，部分资源型区县（珙县、屏山）2024年收入大幅下滑，但支出保持刚性，自给率较2023年明显恶化。</p>

<h3>3.3 市级财政趋势</h3>
<p>2023年全市一般公共预算收入313.99亿元，2024年增长至324.30亿元，增速3.3%。税收占比维持在58.8%左右，财政收入质量相对稳定。2025年1-5月，全市地方一般公共预算收入175.99亿元，同比增长6.4%，开局良好。</p>
<div class="insight-box">
<strong>财政结构亮点：</strong>2024年高技术制造业增加值增长29.3%，晶硅光伏+32.3%、智能网联新能源汽车+27.6%、动力电池+15.0%、酒类+7.7%——"4+4+4"产业体系成为税收增长的新动能。
</div>

<h2>四、文旅发展分析</h2>
<h3>4.1 总体规模</h3>
<p>2024年宜宾市共接待游客9739.82万人次（+9.42%），实现旅游收入898.22亿元（+11.61%）。按全市GDP 4005.76亿元计算，<span class="highlight">旅游收入占GDP比重达22.4%</span>，文旅产业对经济的贡献度较高。</p>

<h3>4.2 区县文旅数据（已披露）</h3>
<table>
<tr><th>区县</th><th>2024年接待游客</th><th>2024年旅游收入</th><th>核心文旅品牌</th></tr>
<tr><td>翠屏区</td><td class="num">3860万人次</td><td class="num">-</td><td>五粮液、李庄古镇（年接待500万+）</td></tr>
<tr><td>长宁县</td><td class="num">1517.58万人次</td><td class="num">154.53亿元</td><td>蜀南竹海、七洞沟、连续3年全国百强</td></tr>
<tr><td>屏山县</td><td class="num">316万人次</td><td class="num">24.65亿元</td><td>八仙山（2024新晋4A）、马湖府古城</td></tr>
<tr><td>兴文县</td><td class="num">-</td><td class="num">-</td><td>兴文石海、僰王山、天府旅游名县</td></tr>
</table>
<div class="insight-box">
<strong>文旅-财政交叉分析：</strong>拥有蜀南竹海、兴文石海等核心4A景区的长宁、兴文两县，2024年财政收入分别仅7.08亿元和15.52亿元，处于全市末位。<strong>文旅资源尚未充分转化为财政实力</strong>，"文旅强、财政弱"现象明显。翠屏区凭借白酒产业+李庄古镇的组合，实现"文旅与财政双高"。
</div>

<h3>4.3 文旅政策与投入</h3>
<p>宜宾市自2019年设立市级文旅发展专项资金以来，年均投入超<span class="highlight">2亿元</span>。2023-2024年累计2457万元文旅消费券资金，撬动消费近亿元。创新"税收反哺"机制，将景区区域市级分成的税收和土地收入反哺景区发展，近两年累计补助李庄景区和"两海"景区1.02亿元。截至2025年7月末，全市文化、体育、娱乐和住宿餐饮业贷款余额达21.82亿元。</p>

<h3>4.4 发展瓶颈</h3>
<p>1. <strong>区县文旅数据披露不充分：</strong>除翠屏、长宁、屏山外，其他区县2024年文旅数据未公开披露，不利于精准施策。</p>
<p>2. <strong>资源转化效率待提升：</strong>核心景区多位于经济欠发达区县，基础设施和配套服务仍有提升空间。</p>
<p>3. <strong>品牌联动不足：</strong>蜀南竹海、兴文石海、李庄古镇等核心景区相对独立，缺乏统一的旅游线路串联和营销整合。</p>
<p>4. <strong>消费转化偏弱：</strong>2024年固投同比-18.4%，社零仅+1.2%，消费市场恢复滞后，文旅消费拉动效果有限。</p>

<h2>五、专题发现：交叉视角</h2>
<h3>5.1 经济结构对比</h3>
<p>翠屏区（2023年）三次产业结构为3.3:64.6:32.1，工业主导特征明显；江安县（2024）为15.2:32.3:52.5，三产已超半数；屏山县（2022）为24.9:35.4:39.7，仍处农业主导阶段。不同区县的产业结构差异巨大，<strong>翠屏是工业驱动型，江安是三产驱动型，屏山是农业驱动型</strong>。</p>

<h3>5.2 财政与文旅的"剪刀差"</h3>
<p>长宁县2024年游客1517.58万人次（占全市15.6%），旅游收入154.53亿元（占全市17.2%），但财政收入仅7.08亿元（占全市2.2%）。反观翠屏区，游客3860万人次，财政收入38亿元，<strong>单位游客创造的财政收入约为长宁的5倍</strong>。差距源于：1）翠屏有白酒税源支撑；2）长宁以观光为主，住宿餐饮等延伸消费不足。</p>

<h3>5.3 增长分化预警</h3>
<p>江安县2024年GDP增速1.4%（全市最低），财政自给率46.2%，但二产占比仅32.3%，主因是房地产低迷+传统工业转型慢。南溪区GDP增速1.8%，财政自给率38.7%，受传统工业转型拖累。需重点关注这两个区县的产业转型路径。</p>

<h2>六、核心结论与建议</h2>
<h3>6.1 核心结论</h3>
<ol>
<li><strong>经济集中度极高：</strong>翠屏区独占全市40.3%的GDP，是叙州区的2.4倍，区县发展不均衡问题突出。</li>
<li><strong>人均GDP分化明显：</strong>仅翠屏区人均GDP（17.42万）超过全国平均水平（9.57万），屏山县仅5.32万元垫底。</li>
<li><strong>财政自给率整体偏低：</strong>9个可比区县中仅翠屏超50%，多数在30%-47%之间，对转移支付依赖较高。</li>
<li><strong>部分区县财政恶化：</strong>珙县（-26.76%）、屏山（-20.42%）、南溪（-7.4%）2024年收入大幅下滑，需警惕财政风险。</li>
<li><strong>文旅贡献显著但转化不足：</strong>旅游收入占GDP 22.4%，但文旅资源富集区长宁/兴文财政排名全市末位，"文旅强、财政弱"现象明显。</li>
<li><strong>产业"4+4+4"成新动能：</strong>晶硅光伏、智能网联新能源汽车、动力电池、酒类增速亮眼，财政质量改善可期。</li>
</ol>

<h3>6.2 政策建议</h3>
<p><strong>对财政方面：</strong></p>
<ul>
<li>优化税收结构，提高税收占比（当前约58.8%），减少非税收入依赖</li>
<li>建立区县财政风险预警机制，重点关注珙县、屏山等收入大幅下滑区县</li>
<li>加大对高技术制造业的财源培育，承接"4+4+4"产业税收落地</li>
</ul>
<p><strong>对文旅方面：</strong></p>
<ul>
<li>建立区县文旅统计强制披露制度，定期公开游客量和旅游收入</li>
<li>推动"文旅+"融合发展，提升景区周边消费带动能力（住宿、餐饮、文创）</li>
<li>构建"蜀南竹海—兴文石海—李庄古镇"精品旅游线路，打造长江文旅统一品牌</li>
<li>支持长宁/兴文等资源富集区县发展"夜经济""研学游""康养游"等延伸业态</li>
<li>借鉴翠屏"工业反哺文旅"经验，探索酒旅融合、茶旅融合新模式</li>
</ul>

<div class="footer">
<p>本报告基于公开政府统计数据整理分析 | 数据更新日期：2026年7月</p>
<p>分析工具：Python + ECharts | 数据来源：宜宾市统计局、财政局、文旅局、各区县统计局</p>
</div>
</body>
</html>
'''
    return html


def generate_readme():
    return '''# 宜宾市各区县财政与文旅数据分析

> 基于 2020-2024 年公开政府统计数据，构建多维度数据可视化与分析体系

## 项目结构

```
.
├── data/
│   ├── yibin_data.json          # 原始数据集（JSON格式）
│   └── yibin_geojson.json       # 宜宾市行政区划边界（GeoJSON）
├── scripts/
│   └── generate_dashboard.py    # 可视化生成脚本
├── dashboard/
│   ├── index.html               # 综合看板（KPI + 7图表 + 数据表）
│   ├── map.html                 # 地图看板（地图 + 时间轴 + 指标切换）
│   └── thematic.html            # 专题分析（文旅-财政交叉视角）
├── report/
│   └── report.html              # 深度分析报告
└── README.md
```

## 可视化模块

### 1. 综合看板 (index.html)
- 全市GDP趋势、4个KPI卡
- 各区县GDP/财政收入排名（2024）
- 5年GDP趋势对比折线图
- 财政自给率、人均GDP
- 全市财政收支趋势
- 交互式数据总表（GDP/财政/文旅三标签）

### 2. 地图看板 (map.html) ⭐ 核心
- **真实宜宾市行政区划地图**（基于阿里 DataV GeoJSON）
- **6大指标切换**：GDP / 财政收入 / 财政自给率 / 人均GDP / 接待游客 / 旅游收入
- **时间轴**：2020-2024 年份滑动切换
- **鼠标悬停**：自动显示该区县详细数据tooltip
- **点击地图**：右侧详情面板更新
- **实时排名榜**：随年份+指标动态变化

### 3. 专题分析 (thematic.html)
- 散点图：文旅资源 vs 财政实力
- 增长动能分组柱图
- 三次产业结构堆叠图
- 区县梯队雷达图
- 4A景区 vs 财政收入双轴图
- 财政自给率 vs 接待游客四象限图

### 4. 分析报告 (report.html)
- 完整深度分析（六大章节）
- 区县GDP多年时间序列表
- 财政自给率详表
- 核心发现 + 政策建议

## 核心发现

| 维度 | 关键结论 |
|------|---------|
| 经济格局 | 翠屏区占全市40.3%GDP，"一城独大" |
| 人均分化 | 仅翠屏超全国均值，屏山垫底（5.32万） |
| 财政自给 | 仅翠屏超50%，多数区县30%-47% |
| 财政风险 | 珙县-26.76%、屏山-20.42% 收入大幅下滑 |
| 文旅转化 | 翠屏单位游客创收5倍于长宁，"文旅强、财政弱"明显 |
| 产业新动能 | 晶硅光伏+32.3%、智能网联+27.6%、动力电池+15.0% |

## 数据来源

- 宜宾市/各区县统计局国民经济和社会发展统计公报
- 宜宾市/各区县财政局财政决算报告
- 宜宾市文旅局假日市场统计
- 2025 年全国县域旅游发展研究报告
- 行政区划边界：阿里 DataV.GeoAtlas

## 技术栈

- **数据处理**：Python 3 + JSON
- **可视化**：ECharts 5（含地图组件）
- **地理数据**：阿里 DataV.GeoAtlas GeoJSON
- **前端**：纯HTML/CSS/JavaScript，零本地依赖

## 使用方式

1. 直接在浏览器中打开 `dashboard/index.html` 查看综合看板
2. 打开 `dashboard/map.html` 进入地图看板（推荐）
3. 打开 `dashboard/thematic.html` 查看专题分析
4. 打开 `report/report.html` 阅读完整分析报告
5. 修改 `data/yibin_data.json` 后运行 `python scripts/generate_dashboard.py` 重新生成

## 许可证

本项目数据来源于政府公开渠道，仅供学习研究使用。
'''


def main():
    print("正在加载数据...")
    data = load_data()
    geojson = load_geojson()

    print("正在计算图表数据...")
    chart_data = compute_chart_data(data)
    rows_gdp, rows_fiscal = build_table_rows(data)

    print("正在生成综合看板...")
    dashboard_html = generate_dashboard(data, chart_data, rows_gdp, rows_fiscal)
    with open(DASHBOARD_PATH, 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    print(f"  ✓ {DASHBOARD_PATH}")

    print("正在生成地图看板...")
    map_html = generate_map_dashboard(data, geojson)
    with open(MAP_PATH, 'w', encoding='utf-8') as f:
        f.write(map_html)
    print(f"  ✓ {MAP_PATH}")

    print("正在生成专题分析页...")
    thematic_html = generate_thematic_dashboard(data)
    with open(THEMATIC_PATH, 'w', encoding='utf-8') as f:
        f.write(thematic_html)
    print(f"  ✓ {THEMATIC_PATH}")

    print("正在生成分析报告...")
    report_html = generate_report(data)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_html)
    print(f"  ✓ {REPORT_PATH}")

    print("正在生成README...")
    readme = generate_readme()
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(readme)
    print(f"  ✓ {README_PATH}")

    print("\n全部生成完成！")
    print(f"  综合看板: file://{DASHBOARD_PATH}")
    print(f"  地图看板: file://{MAP_PATH}")
    print(f"  专题分析: file://{THEMATIC_PATH}")
    print(f"  分析报告: file://{REPORT_PATH}")


if __name__ == '__main__':
    main()
