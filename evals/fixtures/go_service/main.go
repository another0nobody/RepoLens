package main

import (
	"fmt"

	"github.com/gin-gonic/gin"
)

func main() {
	router := gin.Default()
	router.GET("/health", handleHealth)
	fmt.Println("listening on :8080")
	_ = router.Run(":8080")
}
