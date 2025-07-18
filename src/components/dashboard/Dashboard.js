import React, { useState, useEffect, useCallback } from 'react';
import classes from "./Dashboard.module.css"
import Metric from "../metrics/Metrics";
import Table from "../tables/Table";

export default function Dashboard(props){
    const maxBlocksPerPage = 4;//на экране максимально можно отобразить 4 стола
    //const [numTables, setNumTables] =useState(props.num);
    const NumTables=props.num
    const [metrics, setMetrics] = useState([])
    const fetchMetrics = useCallback(async () => {
        const response = await fetch('https://dummyjson.com/c/e480-4f05-46f9-8248')
        const metrics = await response.json()
        setMetrics(metrics)
    }, [])
    useEffect(() => {
        fetchMetrics()
    }, [fetchMetrics])
    //алгоритм для отображения по 4 стола на странице    
    const [currentBlockIndex, setCurrentBlockIndex] = useState(0);
    
    const calculateBlocksToDisplay = (currentIndex) => { //сколько блоков отображать на текущей странице
        return Math.min(maxBlocksPerPage, NumTables - currentIndex); // Возвращаем количество блоков для отображения
    };

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentBlockIndex((prevIndex) => {
                const newIndex = prevIndex + maxBlocksPerPage;
                return newIndex >= NumTables ? 0 : newIndex; // Если превышен NumTables, начинаем заново
            });
        }, 7000);
        
        return () => clearInterval(interval);
    }, [NumTables]);

    const blocksToDisplay = calculateBlocksToDisplay(currentBlockIndex);

    //подгрузка данных о пользователях в текущем раунде
    const [people, setPeople] = useState([])

    const fetchPeople = useCallback(async () => {
        const response = await fetch('https://dummyjson.com/c/7101-d292-4b30-8058')
        const people = await response.json()
        setPeople(people)
    }, [])

    useEffect(() => {
        fetchPeople()
    }, [fetchPeople])

    return (
        <section className={classes.container}>
            <div className={classes.dashboard}>
                <div className={classes.dashboard_text}>
                    <a style={{color:'white', fontSize: '20px', fontWeight: 'bold'}}>Рассадка за столами</a>
                </div>
                {/* table_index -номер стола, рассчитывается здесь,
                    num_tables- число столов, передается с бэка,
                    также с бэка надо передавать список участников и число мест за столами */}
                <div style={{display: 'flex', flexDirection: 'row'}}>
                    <div className={classes.tables}>
                        { [...Array(blocksToDisplay)].map((item, index) => <Table key={index} 
                        table_index={(currentBlockIndex+1)+index} num_tables={NumTables} 
                        num_seats={metrics.map((metric) => (metric.seats[currentBlockIndex+index]))}/> ) } 
                    </div>
                    <div className={classes.names}>
                        <div className={classes.column} style={{borderRight: '1px solid #ccc'}}>
                        <a style={{fontWeight: 'bold', fontSize: '12px'}}>Мнемоника</a>
                        {people
                                .filter(person => (person.table_index <= currentBlockIndex + 4)&&(person.table_index>currentBlockIndex))
                                .map((person, index) => (
                                    <li style={{ listStyle: 'none' }} key={index}>
                                        <a style={{fontWeight: 'bold', fontSize: '10px'}}>{person.initials}</a>
                                    </li>
                                ))}
                        </div>
                        <div className={classes.column} style={{borderRight: '1px solid #ccc'}}>
                        <a style={{fontWeight: 'bold', fontSize: '12px'}}>Участник</a>
                        {people
                                .filter(person => (person.table_index <= currentBlockIndex + 4)&&(person.table_index>currentBlockIndex))
                                .map((person, index) => (
                                    <li style={{ listStyle: 'none' }} key={index}>
                                        <a style={{fontWeight: 'bold', fontSize: '10px'}}>{person.name}</a>
                                    </li>
                                ))}
                        </div>
                        <div className={classes.column}>
                        <a style={{fontWeight: 'bold', fontSize: '12px'}}>Номер стола</a>
                        {people
                                .filter(person => (person.table_index <= currentBlockIndex + 4)&&(person.table_index>currentBlockIndex))
                                .map((person, index) => (
                                    <li style={{listStyle: 'none'}} key={index}>
                                        <a style={{fontWeight: 'bold', fontSize: '10px'}}>{person.table_index}</a>
                                    </li>
                                ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* в этот блок с метриками с бэка передаём процент уникальных встреч, номер раунда, число участников и число столов */}
            <div className={classes.metrics}>
                <Metric  key={1} 
                strangers_num={metrics.map((metric) => (metric.strangers_num))}
                current_round={metrics.map((metric) => (metric.current_round))}
                round={metrics.map((metric) => (metric.round_num))}
                people={metrics.map((metric) => (metric.people_num))}
                tables={metrics.map((metric) => (metric.tables_num))}
                round_time={metrics.map((metric) => (metric.round_time))}
                break_time={metrics.map((metric) => (metric.break_time))}
                />           
            </div>
        </section>
    )
}