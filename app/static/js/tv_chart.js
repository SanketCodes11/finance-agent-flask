class TVChart {
    constructor(containerId, isDarkTheme) {
        this.container = document.getElementById(containerId);
        this.container.style.display = 'flex';
        this.container.style.flexDirection = 'column';
        this.isDark = isDarkTheme;
        
        this.mainContainer = document.createElement('div');
        this.mainContainer.style.flex = '1';
        this.mainContainer.style.minHeight = '400px';
        this.container.appendChild(this.mainContainer);

        const initialWidth = this.container.clientWidth > 0 ? this.container.clientWidth : (this.container.parentElement ? this.container.parentElement.clientWidth : 800);
        const chartOptions = {
            width: initialWidth,
            height: 400,
            layout: {
                background: { type: 'solid', color: this.isDark ? 'rgba(33, 37, 41, 1)' : '#ffffff' },
                textColor: this.isDark ? '#adb5bd' : '#495057',
            },
            grid: {
                vertLines: { color: this.isDark ? '#343a40' : '#e9ecef' },
                horzLines: { color: this.isDark ? '#343a40' : '#e9ecef' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: this.isDark ? '#495057' : '#dee2e6',
                scaleMargins: { top: 0.1, bottom: 0.2 },
            },
            timeScale: {
                borderColor: this.isDark ? '#495057' : '#dee2e6',
                timeVisible: true,
                secondsVisible: false,
            },
        };
        
        this.chart = LightweightCharts.createChart(this.mainContainer, chartOptions);
        this.mainSeries = null;
        this.volumeSeries = null;
        this.indicators = {}; // store indicator series on main chart
        this.panes = {}; // MACD, RSI separate charts
        this.isSyncing = false; // prevents infinite loop during sync
        
        window.addEventListener('resize', () => {
            if (this.chart) {
                this.chart.applyOptions({ width: this.container.clientWidth > 0 ? this.container.clientWidth : 800 });
                Object.values(this.panes).forEach(p => {
                    p.chart.applyOptions({ width: this.container.clientWidth > 0 ? this.container.clientWidth : 800 });
                });
            }
        });

        // Setup main chart timeScale sync emitter
        this.chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (!this.isSyncing && range) {
                this.isSyncing = true;
                Object.values(this.panes).forEach(p => {
                    p.chart.timeScale().setVisibleLogicalRange(range);
                });
                this.isSyncing = false;
            }
        });
        
        // Setup crosshair sync emitter from main chart
        this.chart.subscribeCrosshairMove(param => {
            if (!param.time) return;
            Object.values(this.panes).forEach(p => {
                // In Lightweight Charts, sync crosshair requires converting time to coordinate if you want to use setCrosshairPosition (if supported), 
                // but the time scale is synced so that's the most critical part. 
                // We'll leave crosshair sync implicit via timeScale for simplicity, or just set crosshair if available.
            });
        });
    }

    setTheme(isDark) {
        this.isDark = isDark;
        const themeOptions = {
            layout: {
                background: { type: 'solid', color: this.isDark ? 'rgba(33, 37, 41, 1)' : '#ffffff' },
                textColor: this.isDark ? '#adb5bd' : '#495057',
            },
            grid: {
                vertLines: { color: this.isDark ? '#343a40' : '#e9ecef' },
                horzLines: { color: this.isDark ? '#343a40' : '#e9ecef' },
            },
            rightPriceScale: { borderColor: this.isDark ? '#495057' : '#dee2e6' },
            timeScale: { borderColor: this.isDark ? '#495057' : '#dee2e6' }
        };
        this.chart.applyOptions(themeOptions);
        
        Object.values(this.panes).forEach(p => {
            p.chart.applyOptions(themeOptions);
            p.container.style.borderTop = `1px solid ${this.isDark ? '#343a40' : '#e9ecef'}`;
        });
    }

    setData(data, chartType = 'candle') {
        this.chartData = data;
        
        if (this.mainSeries) {
            this.chart.removeSeries(this.mainSeries);
        }
        if (this.volumeSeries) {
            this.chart.removeSeries(this.volumeSeries);
        }
        
        // Remove old main chart indicators
        Object.values(this.indicators).forEach(series => {
            if (Array.isArray(series)) {
                series.forEach(s => this.chart.removeSeries(s));
            } else {
                this.chart.removeSeries(series);
            }
        });
        this.indicators = {};

        // Remove old panes completely to force a clean redraw
        const activePanes = Object.keys(this.panes);
        activePanes.forEach(type => this.removePane(type));

        // Create main series
        if (chartType === 'candle') {
            this.mainSeries = this.chart.addSeries(LightweightCharts.CandlestickSeries, {
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });
            this.mainSeries.setData(data.map(d => ({
                time: d.time, open: d.open, high: d.high, low: d.low, close: d.close
            })));
        } else if (chartType === 'line') {
            this.mainSeries = this.chart.addSeries(LightweightCharts.LineSeries, {
                color: '#2962FF', lineWidth: 2,
            });
            this.mainSeries.setData(data.map(d => ({ time: d.time, value: d.close })));
        } else if (chartType === 'area') {
            this.mainSeries = this.chart.addSeries(LightweightCharts.AreaSeries, {
                lineColor: '#2962FF', topColor: 'rgba(41, 98, 255, 0.4)', bottomColor: 'rgba(41, 98, 255, 0)',
            });
            this.mainSeries.setData(data.map(d => ({ time: d.time, value: d.close })));
        }

        // Volume series
        this.volumeSeries = this.chart.addSeries(LightweightCharts.HistogramSeries, {
            color: '#26a69a',
            priceFormat: { type: 'volume' },
            priceScaleId: '', // overlay
        });
        this.volumeSeries.priceScale().applyOptions({
            scaleMargins: { top: 0.8, bottom: 0 },
        });
        
        const volumeData = data.map((d, index) => {
            const isUp = index === 0 ? true : d.close >= data[index-1].close;
            return {
                time: d.time,
                value: d.volume,
                color: isUp ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)'
            };
        });
        this.volumeSeries.setData(volumeData);
    }
    
    addIndicator(type, params) {
        if (!this.chartData || this.chartData.length === 0) return;
        
        // Separate panes
        if (type === 'RSI' || type === 'MACD') {
            this.addPane(type, params);
            return;
        }

        const key = type + JSON.stringify(params);
        if (this.indicators[key]) return; // already exists
        
        // Overlays
        if (type === 'SMA') {
            const smaData = calculateSMA(this.chartData, params.period).filter(d => !isNaN(d.value));
            const series = this.chart.addSeries(LightweightCharts.LineSeries, { color: params.color || '#ffeb3b', lineWidth: 2 });
            series.setData(smaData);
            this.indicators[key] = series;
        }
        else if (type === 'EMA') {
            const emaData = calculateEMA(this.chartData, params.period).filter(d => !isNaN(d.value));
            const series = this.chart.addSeries(LightweightCharts.LineSeries, { color: params.color || '#2196f3', lineWidth: 2 });
            series.setData(emaData);
            this.indicators[key] = series;
        }
        else if (type === 'BB') {
            const bb = calculateBollingerBands(this.chartData, params.period, params.stdDev);
            const upper = this.chart.addSeries(LightweightCharts.LineSeries, { color: '#2962FF', lineWidth: 1, lineStyle: 2 });
            const lower = this.chart.addSeries(LightweightCharts.LineSeries, { color: '#2962FF', lineWidth: 1, lineStyle: 2 });
            upper.setData(bb.upper.filter(d => !isNaN(d.value)));
            lower.setData(bb.lower.filter(d => !isNaN(d.value)));
            this.indicators[key] = [upper, lower];
        }
        else if (type === 'VWAP') {
            const vwapData = calculateVWAP(this.chartData).filter(d => !isNaN(d.value));
            const series = this.chart.addSeries(LightweightCharts.LineSeries, { color: '#ff9800', lineWidth: 2 });
            series.setData(vwapData);
            this.indicators[key] = series;
        }
    }

    addPane(type, params) {
        if (this.panes[type]) return; // already exists
        
        const paneContainer = document.createElement('div');
        paneContainer.style.height = '150px';
        paneContainer.style.width = '100%';
        paneContainer.style.borderTop = `1px solid ${this.isDark ? '#343a40' : '#e9ecef'}`;
        this.container.appendChild(paneContainer);
        
        const paneChart = LightweightCharts.createChart(paneContainer, {
            width: this.container.clientWidth,
            height: 150,
            layout: {
                background: { type: 'solid', color: this.isDark ? 'rgba(33, 37, 41, 1)' : '#ffffff' },
                textColor: this.isDark ? '#adb5bd' : '#495057',
            },
            grid: {
                vertLines: { color: this.isDark ? '#343a40' : '#e9ecef' },
                horzLines: { color: this.isDark ? '#343a40' : '#e9ecef' },
            },
            crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
            rightPriceScale: { borderColor: this.isDark ? '#495057' : '#dee2e6' },
            timeScale: {
                borderColor: this.isDark ? '#495057' : '#dee2e6',
                timeVisible: true,
                secondsVisible: false,
            }
        });
        
        // Sync back to main chart
        paneChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
            if (!this.isSyncing && range) {
                this.isSyncing = true;
                this.chart.timeScale().setVisibleLogicalRange(range);
                Object.values(this.panes).forEach(p => {
                    if (p.chart !== paneChart) p.chart.timeScale().setVisibleLogicalRange(range);
                });
                this.isSyncing = false;
            }
        });

        if (type === 'RSI') {
            const period = params.period || 14;
            const rsiData = calculateRSI(this.chartData, period).filter(d => !isNaN(d.value));
            
            // Reference lines
            const topRef = paneChart.addSeries(LightweightCharts.LineSeries, { color: 'rgba(156, 39, 176, 0.3)', lineWidth: 1, lineStyle: 2, lastValueVisible: false, priceLineVisible: false });
            topRef.setData(this.chartData.map(d => ({ time: d.time, value: 70 })));
            
            const botRef = paneChart.addSeries(LightweightCharts.LineSeries, { color: 'rgba(156, 39, 176, 0.3)', lineWidth: 1, lineStyle: 2, lastValueVisible: false, priceLineVisible: false });
            botRef.setData(this.chartData.map(d => ({ time: d.time, value: 30 })));
            
            const rsiSeries = paneChart.addSeries(LightweightCharts.LineSeries, { color: '#9c27b0', lineWidth: 2 });
            rsiSeries.setData(rsiData);
            
            // Force 0-100 scale loosely
            rsiSeries.priceScale().applyOptions({
                autoScale: false,
                scaleMargins: { top: 0.1, bottom: 0.1 },
            });
            paneChart.timeScale().fitContent();
        } else if (type === 'MACD') {
            const macdData = calculateMACD(this.chartData, params.fast || 12, params.slow || 26, params.signal || 9);
            
            const histSeries = paneChart.addSeries(LightweightCharts.HistogramSeries, { color: '#26a69a' });
            histSeries.setData(macdData.histogram.filter(d => !isNaN(d.value)));
            
            const macdSeries = paneChart.addSeries(LightweightCharts.LineSeries, { color: '#2962FF', lineWidth: 2 });
            macdSeries.setData(macdData.macd.filter(d => !isNaN(d.value)));
            
            const signalSeries = paneChart.addSeries(LightweightCharts.LineSeries, { color: '#ff9800', lineWidth: 2 });
            signalSeries.setData(macdData.signal.filter(d => !isNaN(d.value)));
        }
        
        this.panes[type] = { chart: paneChart, container: paneContainer };
        
        // Ensure new pane matches current time scale
        const currentRange = this.chart.timeScale().getVisibleLogicalRange();
        if (currentRange) {
            paneChart.timeScale().setVisibleLogicalRange(currentRange);
        }
    }

    removePane(type) {
        if (this.panes[type]) {
            const pane = this.panes[type];
            pane.chart.remove(); 
            pane.container.remove();
            delete this.panes[type];
        }
    }

    clearIndicators() {
        Object.values(this.indicators).forEach(series => {
            if (Array.isArray(series)) {
                series.forEach(s => this.chart.removeSeries(s));
            } else {
                this.chart.removeSeries(series);
            }
        });
        this.indicators = {};
        
        // Don't auto-remove panes here, wait for toggles to trigger add/remove explicitly
        // or just rely on applyActiveIndicators completely clearing and redrawing.
        // Let's actually remove panes here so it's a full clear.
        Object.keys(this.panes).forEach(type => this.removePane(type));
    }
}
