<?php
/**
 * Router - Simple PHP router with zero dependencies
 *
 * Handles HTTP routing for Biovarase Web
 * Supports GET, POST, PUT, DELETE methods
 * Supports URL parameters like /api/results/{id}
 *
 * Compatible with PHP 7.x
 */

class Router
{
    private $routes = [];
    private $basePath = '';
    private $params = [];

    /**
     * Set base path for all routes (e.g., '/biovarase')
     */
    public function setBasePath($basePath)
    {
        $this->basePath = rtrim($basePath, '/');
    }

    /**
     * Register a GET route
     */
    public function get($path, $handler)
    {
        $this->addRoute('GET', $path, $handler);
    }

    /**
     * Register a POST route
     */
    public function post($path, $handler)
    {
        $this->addRoute('POST', $path, $handler);
    }

    /**
     * Register a PUT route
     */
    public function put($path, $handler)
    {
        $this->addRoute('PUT', $path, $handler);
    }

    /**
     * Register a DELETE route
     */
    public function delete($path, $handler)
    {
        $this->addRoute('DELETE', $path, $handler);
    }

    /**
     * Add route to internal registry
     */
    private function addRoute($method, $path, $handler)
    {
        // Convert {param} to regex pattern
        $pattern = preg_replace('/\{([a-zA-Z_]+)\}/', '(?P<$1>[^/]+)', $path);
        $pattern = '#^' . $pattern . '$#';

        $this->routes[] = [
            'method' => $method,
            'path' => $path,
            'pattern' => $pattern,
            'handler' => $handler
        ];
    }

    /**
     * Get URL parameters extracted from route
     */
    public function getParams()
    {
        return $this->params;
    }

    /**
     * Get single URL parameter
     */
    public function getParam($name, $default = null)
    {
        return isset($this->params[$name]) ? $this->params[$name] : $default;
    }

    /**
     * Run the router - match request and execute handler
     */
    public function run()
    {
        $method = $_SERVER['REQUEST_METHOD'];
        $uri = $this->getUri();

        // Support PUT/DELETE via POST with _method field
        if ($method === 'POST' && isset($_POST['_method'])) {
            $method = strtoupper($_POST['_method']);
        }

        foreach ($this->routes as $route) {
            if ($route['method'] !== $method) {
                continue;
            }

            if (preg_match($route['pattern'], $uri, $matches)) {
                // Extract named parameters
                $this->params = array_filter($matches, function($key) {
                    return is_string($key);
                }, ARRAY_FILTER_USE_KEY);

                $this->executeHandler($route['handler']);
                return;
            }
        }

        // No route matched
        $this->notFound();
    }

    /**
     * Get clean URI without base path and query string
     */
    private function getUri()
    {
        $uri = isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '/';

        // Remove query string
        $pos = strpos($uri, '?');
        if ($pos !== false) {
            $uri = substr($uri, 0, $pos);
        }

        // Remove base path
        if ($this->basePath && strpos($uri, $this->basePath) === 0) {
            $uri = substr($uri, strlen($this->basePath));
        }

        // Ensure leading slash
        if (empty($uri) || $uri[0] !== '/') {
            $uri = '/' . $uri;
        }

        return $uri;
    }

    /**
     * Execute route handler (file include or callable)
     */
    private function executeHandler($handler)
    {
        if (is_callable($handler)) {
            call_user_func($handler, $this);
        } else {
            // Handler is a file path
            $file = __DIR__ . '/../' . ltrim($handler, '/');
            if (file_exists($file)) {
                // Make router available in included file
                $router = $this;
                require $file;
            } else {
                $this->notFound("Handler file not found: $handler");
            }
        }
    }

    /**
     * Send 404 response
     */
    private function notFound($message = 'Route not found')
    {
        http_response_code(404);
        header('Content-Type: application/json');
        echo json_encode([
            'error' => true,
            'message' => $message
        ]);
    }
}
