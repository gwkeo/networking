import React, { useState, useEffect, useCallback } from 'react';
import './Metrics.css'
import Timer from '../timer/Timer';

export default function Metric(props){

    return (
        <metric>
        <div className='metric'>
                <Timer round_time={props.round_time} break_time={props.break_time} />
            
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '12px', }}>Номер раунда</a>
                <a style={{ color: 'white', fontSize: '19px', }}>{props.round}</a>
            </div>
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '12px', }}>Участники</a>
                <a style={{ color: 'white', fontSize: '19px', }}>{props.people}</a>
            </div>
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '12px', }}>Процент уникальных встреч</a>
                <a style={{ color: 'white', fontSize: '19px', }}>{props.unique_meetings}</a>
            </div>
        </div>
        </metric>
    )
}
