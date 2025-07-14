// import logo from './logo.svg';
import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/header/Header';
import Dashboard from "./components/dashboard/Dashboard";
import './App.css';

export default function App() {
    const [metrics, setMetrics] = useState([])
    const fetchMetrics = useCallback(async () => {
        const response = await fetch('https://dummyjson.com/c/210e-986a-455d-90f7')
        const metrics = await response.json()
        setMetrics(metrics)
    }, [])
    useEffect(() => {
        fetchMetrics()
    }, [fetchMetrics]) 
    const numTables = metrics.map((metric) => (metric.tables));
    return (
        <div className="App">
            <Header/>
            <Dashboard key={1} num={numTables}/>
            <footer></footer>
        </div>
    );
}