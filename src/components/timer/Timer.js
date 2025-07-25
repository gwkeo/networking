import React, { useEffect, useState } from 'react';
import './Timer.css'

const Timer = ({ round_time, break_time, session_started }) => {
  // Устанавливаем начальное время в секундах
  const [timeLeft, setTimeLeft] = useState(round_time * 60); // Переводим минуты в секунды
  const [isRoundActive, setIsRoundActive] = useState(true);

  // Сброс таймера при изменении round_time или session_started
  useEffect(() => {
    if (!session_started) {
      setTimeLeft(round_time * 60);
      setIsRoundActive(true);
      return;
    }
    setTimeLeft(round_time * 60);
    setIsRoundActive(true);
  }, [round_time, session_started]);

  useEffect(() => {
    if (!session_started) {
      setTimeLeft(round_time * 60);
      return;
    }

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
  }, [timeLeft, isRoundActive, round_time, break_time, session_started]);

  const minutes = String(Math.floor(timeLeft / 60)).padStart(2, '0');
  const seconds = String(timeLeft % 60).padStart(2, '0');

  return (
    <div className='metric-content'>
      <a className="metricsHeader">
        {session_started
          ? (isRoundActive ? 'До конца раунда осталось' : 'До конца перерыва осталось')
          : 'Ожидание старта сессии...'}
      </a>
      <a className="metricsValue">{minutes}:{seconds}</a>
    </div>
  );
};

export default Timer;
