import React, { useState, useEffect, useCallback } from 'react';
import './Table.css';

export default function Table(props) {
    const [people, setPeople] = useState([])

    const fetchPeople = useCallback(async () => {
        const response = await fetch('https://dummyjson.com/c/7101-d292-4b30-8058')
        const people = await response.json()
        setPeople(people)
    }, [])

    useEffect(() => {
        fetchPeople()
    }, [fetchPeople])

    const radius = 60; // подумать об относительности размера
    const smallCircleRadius = 20; // радиус маленьких кружков

    return (
        <table_container>
           <div className='table_container'>
            <div className="circles">
                <div className="big-circle" style={{ width: radius * 2, height: radius * 2 }}>
                    <span className="circle-number">{props.table_index}</span>
                    {Array.from({ length: props.num_seats }).map((_, i) => {
                    const angle = (i / props.num_seats) * 2 * Math.PI - Math.PI / 2; // угол в радианах
                    const x = radius + radius * Math.cos(angle) - smallCircleRadius; // координата X
                    const y = radius + radius * Math.sin(angle) - smallCircleRadius; // координата Y
                    const filteredNames = people
                        .filter(person => person.table_index === props.table_index)
                        .map(person => person.initials);
                    return (
                        <div
                                key={i}
                                className="small-circle"
                                style={{
                                    left: x,
                                    top: y,
                                    width: smallCircleRadius * 2,
                                    height: smallCircleRadius * 2,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                }}
                            >
                                <span className="circle-number" style={{fontSize: '10px'}}>{filteredNames[i]}</span>
                            </div>
                    );
                    })}
                </div>
            </div>
            {/* <div style={{color: 'white', textAlign: 'left', fontSize: '14px', alignSelf: 'center'}}>
                <ol style={{listStyle: 'none'}}>
                    {names.map((name, index) => (
                        <li key={index} >{props.table_index}.{index + 1 }     { name}</li>
                    ))}
                </ol>
            </div> */}
           
        </div>
        </table_container>
    );
};