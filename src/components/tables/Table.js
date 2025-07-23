import React from 'react';
import './Table.css';

export default function Table(props) {
    const { people, table_index } = props;
    const tablePeople = people.filter(person => person.table_index === table_index);
    const num_seats = tablePeople.length;
    const radius = 60; // Возвращаем исходный размер основного круга
    const smallCircleRadius = 25; // Оставляем увеличенный размер кругов с инициалами
    
    return (
        <table_container>
           <div className='table_container'>
            <div className="circles">
                <div className="big-circle" style={{ width: radius * 2, height: radius * 2 }}>
                    <span className="circle-number" style={{fontSize: '3.5vh'}}>{table_index}</span>
                    {tablePeople.map((person, i) => {
                        const angle = (i / num_seats) * 2 * Math.PI - Math.PI / 2;
                        const x = radius + radius * Math.cos(angle) - smallCircleRadius;
                        const y = radius + radius * Math.sin(angle) - smallCircleRadius;
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
                                <span className="circle-number" style={{
                                    fontSize: '2vh',
                                    position: 'static',
                                    transform: 'none'
                                }}>{person.initials}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
           </div>
        </table_container>
    );
}