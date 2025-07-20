import React from 'react';
import './Table.css';

export default function Table(props) {
    const { people, table_index } = props;
    // Фильтруем пользователей, которые сидят за этим столом
    const tablePeople = people.filter(person => person.table_index === table_index);
    const num_seats = tablePeople.length;
    const radius = 60; // подумать об относительности размера
    const smallCircleRadius = 20; // радиус маленьких кружков

    return (
        <table_container>
           <div className='table_container'>
            <div className="circles">
                <div className="big-circle" style={{ width: radius * 2, height: radius * 2 }}>
                    <span className="circle-number">{table_index}</span>
                    {tablePeople.map((person, i) => {
                        const angle = (i / num_seats) * 2 * Math.PI - Math.PI / 2; // угол в радианах
                        const x = radius + radius * Math.cos(angle) - smallCircleRadius; // координата X
                        const y = radius + radius * Math.sin(angle) - smallCircleRadius; // координата Y
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
                                <span className="circle-number" style={{fontSize: '10px'}}>{person.initials}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
           </div>
        </table_container>
    );
}