/**
 * Technical Indicators for Lightweight Charts
 */

function calculateSMA(data, period) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            result.push({ time: data[i].time, value: NaN });
            continue;
        }
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += data[i - j].close;
        }
        result.push({ time: data[i].time, value: sum / period });
    }
    return result;
}

function calculateEMA(data, period) {
    const result = [];
    const k = 2 / (period + 1);
    let ema = data[0].close;
    
    for (let i = 0; i < data.length; i++) {
        if (i === 0) {
            result.push({ time: data[i].time, value: ema });
            continue;
        }
        ema = data[i].close * k + ema * (1 - k);
        result.push({ time: data[i].time, value: ema });
    }
    return result;
}

function calculateBollingerBands(data, period, stdDev) {
    const result = { upper: [], middle: [], lower: [] };
    const sma = calculateSMA(data, period);
    
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            result.upper.push({ time: data[i].time, value: NaN });
            result.middle.push({ time: data[i].time, value: NaN });
            result.lower.push({ time: data[i].time, value: NaN });
            continue;
        }
        let mean = sma[i].value;
        let varianceSq = 0;
        for (let j = 0; j < period; j++) {
            varianceSq += Math.pow(data[i - j].close - mean, 2);
        }
        const variance = Math.sqrt(varianceSq / period);
        result.middle.push({ time: data[i].time, value: mean });
        result.upper.push({ time: data[i].time, value: mean + variance * stdDev });
        result.lower.push({ time: data[i].time, value: mean - variance * stdDev });
    }
    return result;
}

function calculateRSI(data, period) {
    const result = [];
    let avgGain = 0;
    let avgLoss = 0;

    for (let i = 0; i < data.length; i++) {
        if (i === 0) {
            result.push({ time: data[i].time, value: NaN });
            continue;
        }
        const change = data[i].close - data[i - 1].close;
        const gain = change > 0 ? change : 0;
        const loss = change < 0 ? -change : 0;

        if (i <= period) {
            avgGain += gain / period;
            avgLoss += loss / period;
            if (i === period) {
                const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
                result.push({ time: data[i].time, value: 100 - (100 / (1 + rs)) });
            } else {
                result.push({ time: data[i].time, value: NaN });
            }
            continue;
        }
        
        avgGain = ((avgGain * (period - 1)) + gain) / period;
        avgLoss = ((avgLoss * (period - 1)) + loss) / period;
        const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
        result.push({ time: data[i].time, value: 100 - (100 / (1 + rs)) });
    }
    return result;
}

function calculateMACD(data, fastPeriod, slowPeriod, signalPeriod) {
    const fastEma = calculateEMA(data, fastPeriod);
    const slowEma = calculateEMA(data, slowPeriod);
    const macdLine = [];
    
    for (let i = 0; i < data.length; i++) {
        if (isNaN(fastEma[i].value) || isNaN(slowEma[i].value)) {
            macdLine.push({ time: data[i].time, value: NaN, close: NaN });
        } else {
            macdLine.push({ time: data[i].time, value: fastEma[i].value - slowEma[i].value, close: fastEma[i].value - slowEma[i].value }); // Include close for EMA calculation
        }
    }
    
    const signalLineRaw = calculateEMA(macdLine.filter(d => !isNaN(d.close)), signalPeriod);
    const result = { macd: [], signal: [], histogram: [] };
    let sigIdx = 0;
    
    for (let i = 0; i < data.length; i++) {
        if (isNaN(macdLine[i].value)) {
            result.macd.push({ time: data[i].time, value: NaN });
            result.signal.push({ time: data[i].time, value: NaN });
            result.histogram.push({ time: data[i].time, value: NaN });
        } else {
            const macdVal = macdLine[i].value;
            let sigVal = NaN;
            if (sigIdx < signalLineRaw.length) {
                sigVal = signalLineRaw[sigIdx].value;
                sigIdx++;
            }
            result.macd.push({ time: data[i].time, value: macdVal });
            result.signal.push({ time: data[i].time, value: sigVal });
            
            const histVal = isNaN(sigVal) ? NaN : macdVal - sigVal;
            result.histogram.push({ 
                time: data[i].time, 
                value: histVal,
                color: histVal > 0 ? 'rgba(38, 166, 154, 0.8)' : 'rgba(239, 83, 80, 0.8)'
            });
        }
    }
    return result;
}

function calculateVWAP(data) {
    const result = [];
    let cumVol = 0;
    let cumVolPrice = 0;
    let currentDay = -1;

    for (let i = 0; i < data.length; i++) {
        const d = new Date(data[i].time * 1000);
        const day = d.getDate();
        
        // Reset daily
        if (day !== currentDay) {
            cumVol = 0;
            cumVolPrice = 0;
            currentDay = day;
        }

        const typicalPrice = (data[i].high + data[i].low + data[i].close) / 3;
        cumVol += data[i].volume;
        cumVolPrice += typicalPrice * data[i].volume;

        if (cumVol === 0) {
            result.push({ time: data[i].time, value: data[i].close });
        } else {
            result.push({ time: data[i].time, value: cumVolPrice / cumVol });
        }
    }
    return result;
}
