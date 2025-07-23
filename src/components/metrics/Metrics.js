import React from 'react';
import './Metrics.css'
import Timer from '../timer/Timer';

export default function Metric(props){
    // Функция для безопасного отображения чисел
    const safeNumber = (value) => {
        if (value === undefined || value === null || isNaN(value)) {
            return 0;
        }
        return value;
    };

    // Функция для безопасного отображения процентов
    const safePercentage = (value) => {
        const num = safeNumber(value);
        return num.toFixed(1);
    };

    return (
        <metric>
        <div className='metric'>
                <Timer round_time={safeNumber(props.round_time_minutes)} break_time={safeNumber(props.break_time_minutes)} session_started={props.session_started} />
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '16px', }}>Раунд</a>
                <a style={{ color: 'white', fontSize: '25px', }}>{safeNumber(props.current_round)} / {safeNumber(props.total_rounds)}</a>
            </div>
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '16px', }}>Участники</a>
                <a style={{ color: 'white', fontSize: '25px', }}>{safeNumber(props.people_count)}</a>
            </div>
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '16px', }}>Число незнакомых людей</a>
                <a style={{ color: 'white', fontSize: '25px', }}>{safeNumber(props.strangers_num)}</a>
            </div>
        </div>
        </metric>
    )
}
