<?php
/**
 * Plugin Name: WP Theme Agent — Deploy Receiver
 * Plugin URI:  https://github.com/RajGajjar-01/wp-theme-agent
 * Description: Receives and installs WordPress themes uploaded by the WP Theme Agent AI converter.
 * Version:     1.0.0
 * Author:      Raj Gajjar
 * License:     MIT
 * Text Domain: wp-theme-agent
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

final class WP_Theme_Agent_Deploy {

    private const NAMESPACE = 'wp-theme-agent/v1';
    private const OPTION_KEY = 'wp_theme_agent_secret';

    public function __construct() {
        add_action( 'rest_api_init', array( $this, 'register_routes' ) );
        add_action( 'admin_menu', array( $this, 'add_settings_page' ) );
        add_action( 'admin_init', array( $this, 'register_settings' ) );

        register_activation_hook( __FILE__, array( $this, 'on_activate' ) );
    }

    public function on_activate(): void {
        if ( ! get_option( self::OPTION_KEY ) ) {
            update_option( self::OPTION_KEY, wp_generate_password( 48, false ) );
        }
    }

    public function register_routes(): void {
        register_rest_route( self::NAMESPACE, '/deploy', array(
            'methods'             => 'POST',
            'callback'            => array( $this, 'handle_deploy' ),
            'permission_callback' => array( $this, 'check_permission' ),
        ) );

        register_rest_route( self::NAMESPACE, '/status', array(
            'methods'             => 'GET',
            'callback'            => array( $this, 'handle_status' ),
            'permission_callback' => array( $this, 'check_permission' ),
        ) );
    }

    public function check_permission( \WP_REST_Request $request ) {
        $token = $request->get_header( 'X-WP-Theme-Agent-Token' );
        $stored = get_option( self::OPTION_KEY, '' );

        if ( empty( $stored ) || empty( $token ) || ! hash_equals( $stored, $token ) ) {
            return new \WP_Error(
                'rest_forbidden',
                __( 'Invalid or missing authentication token.', 'wp-theme-agent' ),
                array( 'status' => 403 )
            );
        }

        return true;
    }

    public function handle_deploy( \WP_REST_Request $request ) {
        $files = $request->get_file_params();

        if ( empty( $files['theme_zip'] ) ) {
            return new \WP_Error(
                'missing_file',
                __( 'No theme_zip file provided.', 'wp-theme-agent' ),
                array( 'status' => 400 )
            );
        }

        $file = $files['theme_zip'];

        if ( $file['error'] !== UPLOAD_ERR_OK ) {
            return new \WP_Error(
                'upload_error',
                __( 'File upload error.', 'wp-theme-agent' ),
                array( 'status' => 400 )
            );
        }

        $ext = strtolower( pathinfo( $file['name'], PATHINFO_EXTENSION ) );
        if ( $ext !== 'zip' ) {
            return new \WP_Error(
                'invalid_file',
                __( 'Only ZIP files are accepted.', 'wp-theme-agent' ),
                array( 'status' => 400 )
            );
        }

        if ( ! is_uploaded_file( $file['tmp_name'] ) ) {
            return new \WP_Error(
                'invalid_upload',
                __( 'Invalid file upload.', 'wp-theme-agent' ),
                array( 'status' => 400 )
            );
        }

        require_once ABSPATH . 'wp-admin/includes/file.php';
        WP_Filesystem();
        global $wp_filesystem;

        $theme_dir = get_theme_root();
        $tmp_path  = $file['tmp_name'];

        $result = unzip_file( $tmp_path, $theme_dir );

        if ( is_wp_error( $result ) ) {
            return new \WP_Error(
                'unzip_failed',
                sprintf(
                    __( 'Failed to extract theme: %s', 'wp-theme-agent' ),
                    $result->get_error_message()
                ),
                array( 'status' => 500 )
            );
        }

        $activate = $request->get_param( 'activate' );
        $theme_slug = pathinfo( $file['name'], PATHINFO_FILENAME );
        $activated = false;

        if ( $activate === 'true' || $activate === '1' ) {
            $theme = wp_get_theme( $theme_slug );
            if ( $theme->exists() ) {
                switch_theme( $theme_slug );
                $activated = true;
            }
        }

        wp_clean_themes_cache();

        return rest_ensure_response( array(
            'success'   => true,
            'theme'     => $theme_slug,
            'activated' => $activated,
            'message'   => $activated
                ? sprintf( __( 'Theme "%s" installed and activated.', 'wp-theme-agent' ), $theme_slug )
                : sprintf( __( 'Theme "%s" installed successfully.', 'wp-theme-agent' ), $theme_slug ),
        ) );
    }

    public function handle_status( \WP_REST_Request $request ) {
        $current = wp_get_theme();

        return rest_ensure_response( array(
            'wordpress'     => get_bloginfo( 'version' ),
            'active_theme'  => $current->get( 'Name' ),
            'theme_dir'     => get_theme_root(),
            'plugin_version' => '1.0.0',
        ) );
    }

    public function add_settings_page(): void {
        add_options_page(
            __( 'WP Theme Agent', 'wp-theme-agent' ),
            __( 'WP Theme Agent', 'wp-theme-agent' ),
            'manage_options',
            'wp-theme-agent',
            array( $this, 'render_settings_page' )
        );
    }

    public function register_settings(): void {
        register_setting( 'wp_theme_agent_settings', self::OPTION_KEY, array(
            'type'              => 'string',
            'sanitize_callback' => 'sanitize_text_field',
        ) );
    }

    public function render_settings_page(): void {
        $token = get_option( self::OPTION_KEY, '' );
        $endpoint = rest_url( self::NAMESPACE . '/deploy' );
        ?>
        <div class="wrap">
            <h1><?php esc_html_e( 'WP Theme Agent Settings', 'wp-theme-agent' ); ?></h1>

            <div class="card" style="max-width: 700px; padding: 20px;">
                <h2><?php esc_html_e( 'Deploy Endpoint', 'wp-theme-agent' ); ?></h2>
                <p><code><?php echo esc_html( $endpoint ); ?></code></p>

                <h2><?php esc_html_e( 'Secret Token', 'wp-theme-agent' ); ?></h2>
                <p><?php esc_html_e( 'Copy this token to your WP Theme Agent .env file as WP_SECRET_TOKEN.', 'wp-theme-agent' ); ?></p>

                <form method="post" action="options.php">
                    <?php settings_fields( 'wp_theme_agent_settings' ); ?>
                    <table class="form-table">
                        <tr>
                            <th scope="row">
                                <label for="<?php echo esc_attr( self::OPTION_KEY ); ?>">
                                    <?php esc_html_e( 'Token', 'wp-theme-agent' ); ?>
                                </label>
                            </th>
                            <td>
                                <input type="text"
                                       id="<?php echo esc_attr( self::OPTION_KEY ); ?>"
                                       name="<?php echo esc_attr( self::OPTION_KEY ); ?>"
                                       value="<?php echo esc_attr( $token ); ?>"
                                       class="regular-text"
                                       readonly
                                       onclick="this.select();" />
                                <p class="description">
                                    <?php esc_html_e( 'Auto-generated on plugin activation. Click to select and copy.', 'wp-theme-agent' ); ?>
                                </p>
                            </td>
                        </tr>
                    </table>
                </form>

                <h2><?php esc_html_e( 'Environment Variables', 'wp-theme-agent' ); ?></h2>
                <p><?php esc_html_e( 'Add these to your WP Theme Agent .env file:', 'wp-theme-agent' ); ?></p>
                <pre style="background: #f0f0f0; padding: 12px; border-radius: 4px; overflow-x: auto;">WP_SITE_URL=<?php echo esc_html( home_url() ); ?>
WP_SECRET_TOKEN=<?php echo esc_html( $token ); ?></pre>
            </div>
        </div>
        <?php
    }
}

new WP_Theme_Agent_Deploy();
