import React, { useState, useEffect, useCallback } from 'react';
import classes from "./Dashboard.module.css"
import Table from "../tables/Table";

export default function Dashboard(props){
    const maxBlocksPerPage = 4;//на экране максимально можно отобразить 4 стола
    const [people, setPeople] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState(null)

    // Объединенная функция для загрузки всех данных
    const fetchData = useCallback(async () => {
        try {
            setError(null)
            // Загружаем только пользователей
            const usersResponse = await fetch(`${process.env.REACT_APP_API_URL}/users`)

            if (!usersResponse.ok) {
                throw new Error('Ошибка загрузки данных')
            }

            const peopleData = await usersResponse.json()
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
            <div className={classes.mainContainer}>
                <div className={classes.blocksContainer}>
                    {/* Блок с участниками */}
                    <div className={classes.peopleBlock}>
                        <div className={classes.blockTitle}>Рассадка за столами</div>
                        <div className={classes.peopleColumns}>
                            <div className={classes.columnWithBorder}>
                                <a className={classes.columnHeader}>Мнемоника</a>
                                {people
                                    .filter(person => (person.table_index <= currentBlockIndex + 4)&&(person.table_index>currentBlockIndex))
                                    .map((person, index) => (
                                        <li className={classes.columnItem} key={index}>
                                            <a className={classes.columnText}>{person.initials.toUpperCase()}</a>
                                        </li>
                                    ))}
                            </div>
                            <div className={classes.columnWithBorder}>
                                <a className={classes.columnHeader}>Участник</a>
                                {people
                                    .filter(person => (person.table_index <= currentBlockIndex + 4)&&(person.table_index>currentBlockIndex))
                                    .map((person, index) => (
                                        <li className={classes.columnItem} key={index}>
                                            <a className={classes.columnText}>{person.name}</a>
                                        </li>
                                    ))}
                            </div>
                            <div className={classes.columnSmall}>
                                <a className={classes.columnHeader}>№</a>
                                {people
                                    .filter(person => (person.table_index <= currentBlockIndex + 4)&&(person.table_index>currentBlockIndex))
                                    .map((person, index) => (
                                        <li className={classes.columnItem} key={index}>
                                            <a className={classes.columnText}>{person.table_index}</a>
                                        </li>
                                    ))}
                            </div>
                        </div>
                    </div>
                    {/* Блок с графикой столов */}
                    <div className={classes.tablesBlock}>
                        <div className={classes.blockTitleCentered}>Визуализация столов</div>
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
        </section>
    )
}