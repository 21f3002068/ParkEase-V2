<template>
  <div class="chart-container">
    <h3 v-if="title">{{ title }}</h3>
    <div class="chart-wrapper">
      <canvas 
        ref="chartCanvas" 
        @mousemove="handleMouseMove"
        @mouseleave="handleMouseLeave"
        class="chart-canvas"
      ></canvas>
      <div v-if="tooltip.show" class="chart-tooltip" :style="tooltipStyle">
        <div class="tooltip-label">{{ tooltip.label }}</div>
        <div class="tooltip-value">{{ dataLabel }}: {{ tooltip.value }}</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Chart',
  props: {
    type: {
      type: String,
      required: true,
      validator: value => ['line', 'bar'].includes(value)
    },
    data: {
      type: Array,
      required: true
    },
    labels: {
      type: Array,
      required: true
    },
    title: {
      type: String,
      default: ''
    },
    color: {
      type: String,
      default: '#667eea'
    },
    dataLabel: {
      type: String,
      default: 'Data'
    },
    xAxisLabel: {
      type: String,
      default: ''
    },
    yAxisLabel: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      tooltip: {
        show: false,
        x: 0,
        y: 0,
        label: '',
        value: 0
      },
      hoveredIndex: -1,
      animationProgress: 0
    };
  },
  computed: {
    tooltipStyle() {
      return {
        left: `${this.tooltip.x}px`,
        top: `${this.tooltip.y}px`
      };
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.setupCanvas();
      this.animate();
    });
  },
  watch: {
    data: {
      handler() {
        this.animationProgress = 0;
        this.animate();
      },
      deep: true
    },
    labels() {
      this.animationProgress = 0;
      this.animate();
    }
  },
  methods: {
    setupCanvas() {
      const canvas = this.$refs.chartCanvas;
      if (!canvas) return;
      
      const container = canvas.parentElement;
      canvas.width = container.clientWidth;
      canvas.height = 250;
      
      this.drawChart();
    },

    animate() {
      if (this.animationProgress < 1) {
        this.animationProgress += 0.05;
        this.drawChart();
        requestAnimationFrame(() => this.animate());
      }
    },

    drawChart() {
      const canvas = this.$refs.chartCanvas;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      const width = canvas.width;
      const height = canvas.height;
      const padding = 50;

      ctx.clearRect(0, 0, width, height);

      if (!this.data.length) {
        this.drawNoData(ctx, width, height);
        return;
      }

      if (this.type === 'line') {
        this.drawLineChart(ctx, width, height, padding);
      } else {
        this.drawBarChart(ctx, width, height, padding);
      }
    },

    drawLineChart(ctx, width, height, padding) {
      const maxValue = Math.max(...this.data, 1);
      const stepX = (width - 2 * padding) / (this.data.length - 1 || 1);

      // Draw grid
      this.drawGrid(ctx, width, height, padding);

      // Draw gradient fill
      const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
      gradient.addColorStop(0, this.hexToRgba(this.color, 0.3));
      gradient.addColorStop(1, this.hexToRgba(this.color, 0.0));

      ctx.beginPath();
      this.data.forEach((value, index) => {
        const x = padding + index * stepX;
        const y = height - padding - (value / maxValue) * (height - 2 * padding) * this.animationProgress;
        
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.lineTo(padding + (this.data.length - 1) * stepX, height - padding);
      ctx.lineTo(padding, height - padding);
      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();

      // Draw line
      ctx.beginPath();
      this.data.forEach((value, index) => {
        const x = padding + index * stepX;
        const y = height - padding - (value / maxValue) * (height - 2 * padding) * this.animationProgress;
        
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.strokeStyle = this.color;
      ctx.lineWidth = 3;
      ctx.stroke();

      // Draw points
      this.data.forEach((value, index) => {
        const x = padding + index * stepX;
        const y = height - padding - (value / maxValue) * (height - 2 * padding) * this.animationProgress;
        
        const radius = index === this.hoveredIndex ? 6 : 4;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
      });

      // Draw labels
      this.drawLabels(ctx, width, height, padding, stepX);
    },

    drawBarChart(ctx, width, height, padding) {
      const maxValue = Math.max(...this.data, 1);
      const barWidth = (width - 2 * padding) / this.data.length * 0.7;
      const barSpacing = (width - 2 * padding) / this.data.length * 0.3;

      // Draw grid
      this.drawGrid(ctx, width, height, padding);

      // Draw bars
      this.data.forEach((value, index) => {
        const x = padding + index * (barWidth + barSpacing) + barSpacing / 2;
        const barHeight = (value / maxValue) * (height - 2 * padding) * this.animationProgress;
        const y = height - padding - barHeight;

        const isHovered = index === this.hoveredIndex;
        ctx.fillStyle = isHovered 
          ? this.color 
          : this.hexToRgba(this.color, 0.8);
        
        ctx.fillRect(x, y, barWidth, barHeight);

        // Draw value on top
        if (this.animationProgress > 0.8) {
          ctx.fillStyle = '#666';
          ctx.font = '12px Arial';
          ctx.textAlign = 'center';
          ctx.fillText(value.toString(), x + barWidth / 2, y - 5);
        }
      });

      // Draw labels
      this.drawBarLabels(ctx, width, height, padding, barWidth, barSpacing);
    },

    drawGrid(ctx, width, height, padding) {
      const maxValue = Math.max(...this.data, 1);
      
      ctx.strokeStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.lineWidth = 1;

      // Horizontal lines with Y-axis labels
      for (let i = 0; i <= 5; i++) {
        const y = padding + (height - 2 * padding) * (i / 5);
        const value = Math.round(maxValue * (1 - i / 5));
        
        // Draw grid line
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
        
        // Draw Y-axis label
        ctx.fillStyle = '#666';
        ctx.font = '11px Arial';
        ctx.textAlign = 'right';
        ctx.fillText(value.toString(), padding - 10, y + 4);
      }

      // Axes
      ctx.strokeStyle = '#ddd';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(padding, padding);
      ctx.lineTo(padding, height - padding);
      ctx.lineTo(width - padding, height - padding);
      ctx.stroke();
      
      // Y-axis label (rotated)
      if (this.yAxisLabel) {
        ctx.save();
        ctx.translate(15, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillStyle = '#333';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(this.yAxisLabel, 0, 0);
        ctx.restore();
      }
      
      // X-axis label
      if (this.xAxisLabel) {
        ctx.fillStyle = '#333';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(this.xAxisLabel, width / 2, height - 5);
      }
    },

    drawLabels(ctx, width, height, padding, stepX) {
      ctx.fillStyle = '#666';
      ctx.font = '11px Arial';
      ctx.textAlign = 'center';
      
      this.labels.forEach((label, index) => {
        if (index % Math.ceil(this.labels.length / 6) === 0 || index === this.labels.length - 1) {
          const x = padding + index * stepX;
          ctx.fillText(label, x, height - 20);
        }
      });
    },

    drawBarLabels(ctx, width, height, padding, barWidth, barSpacing) {
      ctx.fillStyle = '#666';
      ctx.font = '10px Arial';
      ctx.textAlign = 'center';
      
      this.labels.forEach((label, index) => {
        const x = padding + index * (barWidth + barSpacing) + barSpacing / 2 + barWidth / 2;
        const truncated = label.length > 10 ? label.substring(0, 10) + '...' : label;
        ctx.fillText(truncated, x, height - 20);
      });
    },

    drawNoData(ctx, width, height) {
      ctx.fillStyle = '#999';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('No data available', width / 2, height / 2);
    },

    handleMouseMove(event) {
      const canvas = this.$refs.chartCanvas;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      const padding = 50;
      const width = canvas.width;
      const height = canvas.height;

      if (this.type === 'line') {
        const stepX = (width - 2 * padding) / (this.data.length - 1 || 1);
        
        let closestIndex = -1;
        let closestDistance = Infinity;

        this.data.forEach((value, index) => {
          const pointX = padding + index * stepX;
          const distance = Math.abs(x - pointX);
          
          if (distance < closestDistance && distance < 20) {
            closestDistance = distance;
            closestIndex = index;
          }
        });

        if (closestIndex !== -1) {
          this.hoveredIndex = closestIndex;
          this.tooltip.show = true;
          this.tooltip.x = event.clientX - rect.left + 10;
          this.tooltip.y = event.clientY - rect.top - 40;
          this.tooltip.label = this.labels[closestIndex];
          this.tooltip.value = this.data[closestIndex];
          this.drawChart();
        } else {
          this.hoveredIndex = -1;
          this.tooltip.show = false;
          this.drawChart();
        }
      } else {
        // Bar chart hover
        const barWidth = (width - 2 * padding) / this.data.length * 0.7;
        const barSpacing = (width - 2 * padding) / this.data.length * 0.3;

        let hoveredBar = -1;
        this.data.forEach((value, index) => {
          const barX = padding + index * (barWidth + barSpacing) + barSpacing / 2;
          if (x >= barX && x <= barX + barWidth) {
            hoveredBar = index;
          }
        });

        if (hoveredBar !== -1) {
          this.hoveredIndex = hoveredBar;
          this.tooltip.show = true;
          this.tooltip.x = event.clientX - rect.left + 10;
          this.tooltip.y = event.clientY - rect.top - 40;
          this.tooltip.label = this.labels[hoveredBar];
          this.tooltip.value = this.data[hoveredBar];
          this.drawChart();
        } else {
          this.hoveredIndex = -1;
          this.tooltip.show = false;
          this.drawChart();
        }
      }
    },

    handleMouseLeave() {
      this.hoveredIndex = -1;
      this.tooltip.show = false;
      this.drawChart();
    },

    hexToRgba(hex, alpha) {
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
  }
}
</script>

<style scoped>
.chart-container {
  margin: 20px 0;
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.chart-container h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1rem;
  font-weight: 600;
}

.chart-wrapper {
  position: relative;
  width: 100%;
}

.chart-canvas {
  width: 100%;
  cursor: crosshair;
}

.chart-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  pointer-events: none;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

.tooltip-label {
  font-weight: 600;
  margin-bottom: 2px;
}

.tooltip-value {
  color: #ddd;
  font-size: 11px;
}
</style>