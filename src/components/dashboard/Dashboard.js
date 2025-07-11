import React, { useState, useEffect } from 'react';
import classes from "./Dashboard.module.css"
import Metric from "../metrics/Metrics";
import Table from "../tables/Table";

export default function Dashboard(){
    //что должно будет передаватся с бэка
    //const num_tables = 10; //количество столов - пока задано статически, потом будет передаватся с бэка
    const [NumTables, setNumTables] =useState(7);
    const maxBlocksPerPage = 4;//на экране максимально можно отобразить 4 стола
    //const num_tables = Numtables;
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
    }, []);

    const blocksToDisplay = calculateBlocksToDisplay(currentBlockIndex);

    return (
        <section className={classes.container}>
            <div className={classes.dashboard}>
                <div className={classes.dashboard_text}>
                    <a style={{color:'white', fontSize: '20px', fontWeight: 'bold'}}>Рассадка за столами</a>
                </div>
                {/* table_index -номер стола, рассчитывается здесь,
                    num_tables- число столов, передается с бэка,
                    также с бэка надо передавать список участников и число мест за столами */}
                <div className={classes.tables}>
                    { [...Array(blocksToDisplay)].map((item, index) => <Table key={index} 
                    table_index={(currentBlockIndex+1)+index} num_tables={NumTables} 
                    num_seats={6}/> ) } 
                </div>
            </div>
            
            {/* в этот блок с метриками с бэка передаём процент уникальных встреч, номер раунда, число участников и число столов */}
            <div className={classes.metrics}>
                <Metric/>           
            </div>
        </section>
    )
}
