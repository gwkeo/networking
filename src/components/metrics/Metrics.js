import './Metrics.css'

export default function Metric(props){
    //здесь вместо слова цифра нужно подставить значения с бэка
    return (
        <metric>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '12px', }}>Процент уникальных встреч</a>
                <a style={{ color: 'white', fontSize: '12px', }}>Цифра</a>
            </div>
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '12px', }}>Номер раунда</a>
                <a style={{ color: 'white', fontSize: '12px', }}>Цифра</a>
            </div>
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '12px', }}>Участники</a>
                <a style={{ color: 'white', fontSize: '12px', }}>Цифра</a>
            </div>
        </div>
        <div className='metric'>
            <div className='metric-content'>
                <a style={{ color: 'white', fontSize: '12px', }}>Столы</a>
                <a style={{ color: 'white', fontSize: '12px', }}>Цифра</a>
            </div>
        </div>
        </metric>
    )
}
