import React, { useState, useEffect, useCallback } from 'react';
import classes from "./Dashboard.module.css"
import Metric from "../metrics/Metrics";
import Table from "../tables/Table";

export default function Dashboard(props){
    const maxBlocksPerPage = 4;//на экране максимально можно отобразить 4 стола
    const [metrics, setMetrics] = useState({})
    const [people, setPeople] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)

    // Объединенная функция для загрузки всех данных
    const fetchData = useCallback(async () => {
        try {
            setError(null)
            
            // Параллельно загружаем метрики и пользователей
            const [metricsResponse, usersResponse] = await Promise.all([
                fetch(`${process.env.REACT_APP_API_URL}/metrics`),
                fetch(`${process.env.REACT_APP_API_URL}/users`)
            ])

            if (!metricsResponse.ok || !usersResponse.ok) {
                throw new Error('Ошибка загрузки данных')
            }

            const [metricsData, peopleData] = await Promise.all([
                metricsResponse.json(),
                usersResponse.json()
            ])

            setMetrics(metricsData)
            setPeople(peopleData)
            setIsLoading(false)
        } catch (err) {
            console.error('Ошибка при загрузке данных:', err)
            setError(err.message)
            setIsLoading(false)
        }
    }, [])

    // Начальная загрузка
    useEffect(() => {
        fetchData()
    }, [fetchData])

    // Long polling - каждые 5 секунд обновляем данные
    useEffect(() => {
        const interval = setInterval(() => {
            fetchData()
        }, 5000)

        return () => clearInterval(interval)
    }, [fetchData])

    // вычисляем максимальный номер стола среди пользователей
    const maxTableIndex = people.length > 0 ? Math.max(...people.map(p => p.table_index)) : 0;
    
    // пагинация столов
    const [currentBlockIndex, setCurrentBlockIndex] = useState(0);
    const calculateBlocksToDisplay = (currentIndex) => {
        return Math.min(maxBlocksPerPage, maxTableIndex - currentIndex);
    };
    
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentBlockIndex((prevIndex) => {
                const newIndex = prevIndex + maxBlocksPerPage;
                return newIndex >= maxTableIndex ? 0 : newIndex;
            });
        }, 7000);
        return () => clearInterval(interval);
    }, [maxTableIndex]);
    
    const blocksToDisplay = calculateBlocksToDisplay(currentBlockIndex);

    // Показываем индикатор загрузки при первой загрузке
    if (isLoading) {
        return (
            <section className={classes.container}>
                <div style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    height: '100vh',
                    color: 'white',
                    fontSize: '18px'
                }}>
                    Загрузка данных...
                </div>
            </section>
        )
    }

    // Показываем ошибку, если что-то пошло не так
    if (error) {
        return (
            <section className={classes.container}>
                <div style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    height: '100vh',
                    color: 'red',
                    fontSize: '16px',
                    textAlign: 'center'
                }}>
                    Ошибка загрузки: {error}<br/>
                    <button 
                        onClick={fetchData}
                        style={{
                            marginTop: '20px',
                            padding: '10px 20px',
                            backgroundColor: '#A368FC',
                            color: 'white',
                            border: 'none',
                            borderRadius: '5px',
                            cursor: 'pointer'
                        }}
                    >
                        Попробовать снова
                    </button>
                </div>
            </section>
        )
    }

    return (
        <section className={classes.container}>
            <div className={classes.dashboard}>
                <div className={classes.dashboard_text}>
                <a style={{color:'white', fontSize: '20px', fontWeight: 'bold'}}>Рассадка за столами</a>
                <div style={{color:'#888', fontSize: '12px', marginTop: '5px'}}>Автообновление каждые 5 секунд</div>
                </div>
                <div style={{display: 'flex', flexDirection: 'row'}}>
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
                    <div className={classes.tables}>
                        {Array.from({length: blocksToDisplay}).map((_, index) => {
                            const tableIndex = currentBlockIndex + 1 + index;
                            return (
                                <Table key={tableIndex}
                                    table_index={tableIndex}
                                    people={people}
                                />
                            );
                        })}
                    </div>

                </div>
            </div>
            <div className={classes.metrics}>
                <Metric  key={1} 
                strangers_num={metrics.strangers_num}
                current_round={metrics.current_round}
                total_rounds={metrics.total_rounds}
                people_count={people.length}
                round_time_minutes={metrics.round_time_minutes}
                break_time_minutes={metrics.break_time_minutes}
                />           
            </div>
        </section>
    )
}