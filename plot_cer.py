import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Heiti TC', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

# 数据
conditions = ['安静环境\n(SNR=20dB)', '轻度噪声\n(SNR=10dB)', '强噪声/音乐\n(SNR=0dB)']
cer_values = [3.2, 8.5, 22.0]
colors = ['#4CAF50', '#FF9800', '#f44336']

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(conditions, cer_values, color=colors, edgecolor='black', linewidth=1.5)

for bar, val in zip(bars, cer_values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val}%', ha='center', va='bottom', fontsize=14, fontweight='bold')

ax.set_ylabel('字错误率 CER (%)', fontsize=13)
ax.set_title('不同噪声水平下的语音识别错误率 (CER)', fontsize=15, fontweight='bold')
ax.set_ylim(0, 28)
ax.grid(axis='y', linestyle='--', alpha=0.3)

plt.tight_layout()
plt.savefig('cer_chart.png', dpi=300, bbox_inches='tight')
print("✅ 图片已保存为 cer_chart.png")