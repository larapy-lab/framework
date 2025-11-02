<!DOCTYPE html>
<html>
<head>
    <title>@yield('title', 'Default Title')</title>
</head>
<body>
    <header>
        <h1>Site Header</h1>
    </header>
    
    <main>
        @yield('content')
    </main>
    
    <footer>
        <p>Site Footer</p>
    </footer>
</body>
</html>