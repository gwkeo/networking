import './Header.css'
import logo from '../../static/logo.svg';

export default function Header(){
    return (
        <header>
            <img src={logo} alt="Логотип" className="header-logo" />
            <a className="header-title">Платформа для нетворкинг сессии</a>
        </header>
    )
}
