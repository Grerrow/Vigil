import { NavLink } from 'react-router-dom'


function NavBar() {
  return (
    <nav className="navbar">
      <span className="navbar-brand">
        <span className="brand-dot" />
        VIGIL
      </span>
      <NavLink to="/" end>
        Detection
      </NavLink>
      <NavLink to="/history">History</NavLink>
    </nav>
  )
}

export default NavBar
