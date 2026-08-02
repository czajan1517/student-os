import MainLayout from "./layouts/MainLayout";
import {
    BrowserRouter,
    Routes,
    Route
} from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Calendar from "./pages/Calendar";
import Tasks from "./pages/Tasks";
import Chat from "./pages/Chat";
import Settings from "./pages/Settings";

function App() {
    return (
        <BrowserRouter>
         <Routes>
        <Route path="/" element={<MainLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="calendar" element={<Calendar />} />
        <Route path="Tasks" element={<Tasks />} />
        <Route path="Chat" element={<Chat />} />
        <Route path="Settings" element={<Settings />} />
          </Route>
    </Routes>
    </BrowserRouter>
    )
}

export default App;
