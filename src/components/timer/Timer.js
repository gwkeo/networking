import React, { useEffect, useState } from 'react';
import './Timer.css'

const Timer = ({ round_time, break_time }) => {
  // Устанавливаем начальное время в секундах
  const [timeLeft, setTimeLeft] = useState(round_time * 60); // Переводим минуты в секунды
  const [isRoundActive, setIsRoundActive] = useState(true);

  useEffect(() => {
    const timerId = setInterval(() => {
      setTimeLeft((prevTime) => {
        if (prevTime > 0) {
          return prevTime - 1;
        } else {
          // Если время раунда истекло, переключаемся на перерыв
          if (isRoundActive) {
            setIsRoundActive(false);
            return break_time * 60; // Устанавливаем время перерыва в секундах
          } else {
            // Если время перерыва истекло, переключаемся на раунд
            setIsRoundActive(true);
            return round_time * 60; // Устанавливаем время раунда в секундах
          }
        }
      });
    }, 1000);

    // Очищаем интервал при размонтировании компонента
    return () => clearInterval(timerId);
  }, [timeLeft, isRoundActive, round_time, break_time]);

  const minutes = String(Math.floor(timeLeft / 60)).padStart(2, '0');
  const seconds = String(timeLeft % 60).padStart(2, '0');

  return (
    <div className='metric-content'>
      <a style={{ color: 'white', fontSize: '16px', }}>{isRoundActive ? 'До конца раунда осталось' : 'До конца перерыва осталось'}</a>
      <a style={{ color: 'white', fontSize: '25px', }}>{minutes}:{seconds}</a>
    </div>
  );
};

export default Timer;
