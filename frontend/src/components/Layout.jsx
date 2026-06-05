import { NavLink, Outlet } from 'react-router-dom';
import {
  Home,
  Stethoscope,
  Clock,
  Database,
  BookOpen,
  Fish,
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Beranda', icon: Home },
  { to: '/diagnosis', label: 'Diagnosis', icon: Stethoscope },
  { to: '/riwayat', label: 'Riwayat', icon: Clock },
  { to: '/basis-kasus', label: 'Basis Kasus', icon: Database },
  { to: '/basis-aturan', label: 'Basis Aturan', icon: BookOpen },
];

export default function Layout() {
  return (
    <>
      {/* Sidebar — Desktop */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <Fish size={22} />
          </div>
          <div className="sidebar-brand-text">
            <h2>AquaCase</h2>
            <p>Expert System</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
            >
              <item.icon className="sidebar-link-icon" size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div style={{
          padding: '16px 12px',
          borderTop: '1px solid rgba(0,0,0,0.06)',
          marginTop: 'auto',
        }}>
          <p style={{
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            lineHeight: 1.5,
          }}>
            Hybrid CBR + RBR Engine
            <br />
            v1.0.0
          </p>
        </div>
      </aside>

      {/* Bottom Navbar — Mobile */}
      <nav className="bottomnav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `bottomnav-link ${isActive ? 'active' : ''}`
            }
          >
            <item.icon className="bottomnav-icon" size={22} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>
    </>
  );
}
