// import logo from './logo.svg';
import Header from './components/header/Header';
import Dashboard from "./components/dashboard/Dashboard";
import './App.css';

export default function App() {

    return (
        <div className="App">
            <Header/>
            <Dashboard/>
            <footer></footer>
        </div>
    );
}