import { useEffect, useRef, useState } from "react";
import {
  ArrowLeftRight,
  BarChart3,
  Bell,
  Boxes,
  ClipboardList,
  LayoutDashboard,
  Menu,
  Package,
  Search,
  Settings,
  TriangleAlert,
  UserRound,
  X,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import { getErrorMessage } from "../services/api.js";

const navigation = [
  { label: "Overview", path: "/", icon: LayoutDashboard, end: true },
  { label: "Items", path: "/items", icon: Package },
  { label: "Stock Management", path: "/stock", icon: Boxes },
  { label: "Stock Transactions", path: "/transactions", icon: ArrowLeftRight },
  { label: "Low Stock Alerts", path: "/low-stock", icon: TriangleAlert },
  { label: "Reports", path: "/reports", icon: BarChart3 },
  { label: "Audit Logs", path: "/audit-logs", icon: ClipboardList },
  { label: "Settings", path: "/settings", icon: Settings },
];

function pageTitle(pathname) {
  return navigation.find((item) => item.path === pathname)?.label ?? "Overview";
}

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [globalSearch, setGlobalSearch] = useState("");
  const [openHeaderPanel, setOpenHeaderPanel] = useState(null);
  const [signOutError, setSignOutError] = useState("");
  const headerActionsRef = useRef(null);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  useEffect(() => {
    setMobileOpen(false);
    setOpenHeaderPanel(null);
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobileOpen]);

  useEffect(() => {
    if (!openHeaderPanel) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setOpenHeaderPanel(null);
    };
    const closeOnOutsideClick = (event) => {
      if (!headerActionsRef.current?.contains(event.target)) {
        setOpenHeaderPanel(null);
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    document.addEventListener("pointerdown", closeOnOutsideClick);
    return () => {
      window.removeEventListener("keydown", closeOnEscape);
      document.removeEventListener("pointerdown", closeOnOutsideClick);
    };
  }, [openHeaderPanel]);

  return (
    <div className="app-shell">
      {mobileOpen && (
        <button
          className="sidebar-scrim"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`} id="primary-navigation">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <Boxes size={21} />
          </div>
          <div className="brand-copy">
            <span className="brand-name">Inventory Desk</span>
            <span className="brand-caption">STOCK CONTROL</span>
          </div>
          <button
            className="icon-button sidebar-close"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          >
            <X size={19} />
          </button>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>
        <nav className="nav-list" aria-label="Main navigation">
          {navigation.map(({ label, path, icon: Icon, end }) => (
            <NavLink
              key={path}
              to={path}
              end={end}
              className={({ isActive }) => `nav-link${isActive ? " nav-link-active" : ""}`}
            >
              <Icon size={18} strokeWidth={1.9} aria-hidden="true" />
              <span>{label}</span>
              {label === "Low Stock Alerts" && (
                <span className="nav-dot" aria-label="Review low stock page" />
              )}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <div className="help-icon"><ClipboardList size={17} /></div>
            <div>
              <strong>Learning project</strong>
              <span>MySQL-backed demo</span>
            </div>
          </div>
          <div className="sidebar-version">INVENTORY DESK · LOCAL</div>
        </div>
      </aside>

      <div className="main-column">
        <header className="topbar">
          <div className="topbar-leading">
            <button
              className="icon-button mobile-menu-button"
              aria-label="Open navigation"
              aria-controls="primary-navigation"
              aria-expanded={mobileOpen}
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={21} />
            </button>
            <div className="breadcrumb">
              <span>Workspace</span>
              <span className="breadcrumb-divider">/</span>
              <strong>{pageTitle(location.pathname)}</strong>
            </div>
          </div>
          <div className="topbar-actions" ref={headerActionsRef}>
            <form
              className="global-search"
              role="search"
              onSubmit={(event) => {
                event.preventDefault();
                const query = globalSearch.trim();
                if (query) navigate(`/items?search=${encodeURIComponent(query)}`);
              }}
            >
              <Search size={17} aria-hidden="true" />
              <input
                aria-label="Search inventory by item or SKU"
                placeholder="Search inventory..."
                value={globalSearch}
                onChange={(event) => setGlobalSearch(event.target.value)}
              />
              <kbd>/</kbd>
            </form>
            <div className="header-popover-anchor">
              <button
                className="icon-button notification-button"
                aria-label="Notifications"
                aria-expanded={openHeaderPanel === "notifications"}
                aria-controls="notifications-popover"
                title="Notifications"
                onClick={() => setOpenHeaderPanel(
                  openHeaderPanel === "notifications" ? null : "notifications",
                )}
              >
                <Bell size={19} />
              </button>
              {openHeaderPanel === "notifications" && (
                <section
                  className="header-popover notification-popover"
                  id="notifications-popover"
                  aria-label="Notifications"
                >
                  <strong>Notifications</strong>
                  <p>Notifications are not enabled in this local demo. Review current stock warnings on the Low Stock Alerts page.</p>
                  <NavLink
                    className="header-popover-link"
                    to="/low-stock"
                    onClick={() => setOpenHeaderPanel(null)}
                  >
                    View low-stock alerts
                  </NavLink>
                </section>
              )}
            </div>
            <div className="header-popover-anchor profile-anchor">
              <button
                className="profile-chip"
                aria-label={`${user.full_name} account`}
                aria-expanded={openHeaderPanel === "profile"}
                aria-controls="profile-popover"
                onClick={() => setOpenHeaderPanel(
                  openHeaderPanel === "profile" ? null : "profile",
                )}
              >
                <span className="profile-avatar">
                  {user.full_name.trim().charAt(0).toUpperCase() || <UserRound size={17} />}
                </span>
                <span className="profile-copy">
                  <strong>{user.full_name}</strong>
                  <span>{user.email}</span>
                </span>
              </button>
              {openHeaderPanel === "profile" && (
                <section
                  className="header-popover profile-popover"
                  id="profile-popover"
                  aria-label="Profile"
                >
                  <strong>{user.full_name}</strong>
                  <p>{user.email}</p>
                  <span className={`profile-verification${user.email_verified ? " profile-verified" : ""}`}>
                    {user.email_verified ? "Verified account" : "Email not verified"}
                  </span>
                  {signOutError && <p className="profile-error" role="alert">{signOutError}</p>}
                  <NavLink
                    className="header-popover-link"
                    to="/settings"
                    onClick={() => setOpenHeaderPanel(null)}
                  >
                    Account settings
                  </NavLink>
                  <button
                    className="profile-signout"
                    onClick={async () => {
                      try {
                        setSignOutError("");
                        await signOut();
                        navigate("/login", { replace: true });
                      } catch (error) {
                        setSignOutError(getErrorMessage(error));
                      }
                    }}
                  >
                    Sign out
                  </button>
                </section>
              )}
            </div>
          </div>
        </header>

        <main
          className={`page-content${location.pathname === "/" ? "" : " workspace-page-content"}`}
          id="main-content"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
