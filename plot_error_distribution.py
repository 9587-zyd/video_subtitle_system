import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免PyCharm后端错误
import matplotlib.pyplot as plt
import numpy as np
import os

# 设置中文字体（Windows使用SimHei，Mac使用Heiti TC，Linux使用WenQuanYi）
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
except:
    pass

# 数据：误差区间和占比
ranges = ['< 50ms', '50-100ms', '100-200ms', '> 200ms']
percentages = [65, 22, 10, 3]
colors = ['#4CAF50', '#2196F3', '#FF9800', '#f44336']

# 创建图形
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 左图：饼图
wedges, texts, autotexts = ax1.pie(percentages, labels=ranges, autopct='%1.0f%%',
                                    colors=colors, startangle=90,
                                    textprops={'fontsize': 12})
ax1.set_title('时间轴误差分布 (饼图)', fontsize=14, fontweight='bold')

# 右图：柱状图
bars = ax2.bar(ranges, percentages, color=colors, edgecolor='black', linewidth=1.5)
for bar, val in zip(bars, percentages):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{val}%', ha='center', va='bottom', fontsize=13, fontweight='bold')
ax2.set_ylabel('占比 (%)', fontsize=12)
ax2.set_title('时间轴误差分布 (柱状图)', fontsize=14, fontweight='bold')
ax2.set_ylim(0, 75)
ax2.grid(axis='y', linestyle='--', alpha=0.3)

plt.tight_layout()
# 保存图片，不显示（避免后端错误）
output_path = 'error_distribution.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"✅ 图片已保存为 {output_path}")