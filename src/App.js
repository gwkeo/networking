// import logo from './logo.svg';
import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/header/Header';
import Dashboard from "./components/dashboard/Dashboard";
import './App.css';

export default function App() {
    const [metrics, setMetrics] = useState([])
    const fetchMetrics = useCallback(async () => {
        const response = await fetch('http://localhost:5000/api/metrics')
        const metrics = await response.json()
        setMetrics(metrics)
    }, [])
    useEffect(() => {
        fetchMetrics()
    }, [fetchMetrics]) 
    return (
        <div className="App">
            <Header/>
            <Dashboard key={1}/>
            <footer></footer>
        </div>
    );
}