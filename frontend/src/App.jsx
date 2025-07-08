import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import LoadingScreen from "./components/LoadingScreen.jsx";
import Home from "./components/Home.jsx";
import LaLigaPrediction from "./components/LaLigaPrediction.jsx";
import EPLPrediction from "./components/EPLPrediction.jsx";

export default function App() {
    const [isLoading, setIsLoading] = useState(true);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const start = Date.now();
        const timer = setInterval(() => {
        const elapsed = Date.now() - start;
        setProgress(Math.min(100, (elapsed / 6000) * 100));
        }, 100);

        const timeout = setTimeout(() => {
        clearInterval(timer);
        setIsLoading(false);
        }, 6000);

        return () => {
        clearInterval(timer);
        clearTimeout(timeout);
        };
    }, []);

    if (isLoading) {
        return <LoadingScreen progress={progress} />;
    }

    return (
        <Router>
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/laliga" element={<LaLigaPrediction />} />
            <Route path="/epl" element={<EPLPrediction />} />
            {/* You can add a 404 route later if needed */}
        </Routes>
        </Router>
    );
}
