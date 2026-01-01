// Theme management
class ThemeManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.applyTheme(this.theme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.theme = theme;
    }

    toggle() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        return newTheme;
    }

    getTheme() {
        return this.theme;
    }
}

// Global theme manager
const themeManager = new ThemeManager();

